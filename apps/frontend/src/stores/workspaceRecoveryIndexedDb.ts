import {
  parseRecoveryRecord,
  type RecoveryKey,
  type RecoveryRecordV2,
  type RecoveryStorageLoad,
} from "@/contracts/workspace-recovery";

export class RecoveryStorageError extends Error {
  readonly kind: "unavailable" | "invalid" | "conflict";
  constructor(kind: "unavailable" | "invalid" | "conflict") {
    super(`Recovery storage: ${kind}`);
    this.kind = kind;
  }
}
export interface RecoveryStorage {
  list(actorId: string): Promise<RecoveryStorageLoad>;
  insert(record: RecoveryRecordV2): Promise<void>;
  replace(record: RecoveryRecordV2, expectedRevision: number): Promise<void>;
  remove(
    key: RecoveryKey,
    commandId: string,
    expectedRevision: number,
  ): Promise<void>;
  importLegacy(
    record: RecoveryRecordV2,
    legacyPayload: string,
  ): Promise<"imported" | "already-imported">;
  acknowledgeLegacyRemoval(actorId: string, commandId: string): Promise<void>;
}
const DB = "geoservice-workspace-recovery";
function request<T>(req: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
async function open(): Promise<IDBDatabase> {
  if (!globalThis.indexedDB) throw new RecoveryStorageError("unavailable");
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => {
      const store = req.result.createObjectStore("recoveries", {
        keyPath: "key",
      });
      store.createIndex("actor", "command.actorId");
      req.result.createObjectStore("legacyImports", { keyPath: "id" });
    };
    req.onerror = () => reject(new RecoveryStorageError("unavailable"));
    req.onblocked = () => reject(new RecoveryStorageError("unavailable"));
    req.onsuccess = () => {
      req.result.onversionchange = () => req.result.close();
      resolve(req.result);
    };
  });
}
async function transaction<T>(
  mode: IDBTransactionMode,
  action: (tx: IDBTransaction) => Promise<T>,
): Promise<T> {
  const db = await open();
  return new Promise<T>((resolve, reject) => {
    const tx = db.transaction(["recoveries", "legacyImports"], mode);
    let result: T, failure: unknown;
    tx.oncomplete = () => {
      db.close();
      resolve(result);
    };
    tx.onabort = () => {
      db.close();
      reject(failure ?? new RecoveryStorageError("unavailable"));
    };
    void action(tx)
      .then((value) => {
        result = value;
      })
      .catch((error) => {
        failure = error;
        try {
          tx.abort();
        } catch {
          db.close();
          reject(error);
        }
      });
  });
}
function plain(record: RecoveryRecordV2): RecoveryRecordV2 {
  const value = JSON.parse(JSON.stringify(record));
  return parseRecoveryRecord(value, record.command.actorId);
}
function sameCommand(a: RecoveryRecordV2, b: RecoveryRecordV2): boolean {
  return JSON.stringify(a.command) === JSON.stringify(b.command);
}
export function createRecoveryStorage(): RecoveryStorage {
  return {
    list(actorId) {
      return transaction("readonly", async (tx) => {
        const rows: unknown[] = await request(
          tx.objectStore("recoveries").getAll(),
        );
        const result: RecoveryStorageLoad = { records: [], invalid: [] };
        for (const row of rows) {
          const raw = row as Partial<RecoveryRecordV2>;
          let identity: unknown;
          try {
            identity = JSON.parse(String(raw.key));
          } catch {
            /* unidentifiable record */
          }
          const identifiable =
            Array.isArray(identity) &&
            identity.length === 3 &&
            identity.every((x) => typeof x === "string" && x.length > 0);
          if (identifiable && (identity as string[])[0] !== actorId) continue;
          try {
            result.records.push(plain(parseRecoveryRecord(row, actorId)));
          } catch {
            result.invalid.push({
              key: identifiable ? String(raw.key) : null,
              reason: "invalid",
            });
          }
        }
        return result;
      });
    },
    insert(record) {
      const value = plain(record);
      return transaction("readwrite", async (tx) => {
        const store = tx.objectStore("recoveries");
        if (await request(store.get(value.key)))
          throw new RecoveryStorageError("conflict");
        await request(store.add(value));
      });
    },
    replace(record, expectedRevision) {
      const value = plain(record);
      return transaction("readwrite", async (tx) => {
        const store = tx.objectStore("recoveries");
        const previous = (await request(store.get(value.key))) as
          | RecoveryRecordV2
          | undefined;
        if (
          !previous ||
          previous.revision !== expectedRevision ||
          value.revision !== expectedRevision + 1 ||
          !sameCommand(previous, value)
        )
          throw new RecoveryStorageError("conflict");
        await request(store.put(value));
      });
    },
    remove(key, commandId, expectedRevision) {
      return transaction("readwrite", async (tx) => {
        const store = tx.objectStore("recoveries");
        const previous = (await request(store.get(key))) as
          | RecoveryRecordV2
          | undefined;
        if (
          !previous ||
          previous.revision !== expectedRevision ||
          previous.command.request.commandId !== commandId
        )
          throw new RecoveryStorageError("conflict");
        await request(store.delete(key));
      });
    },
    importLegacy(record, legacyPayload) {
      const value = plain(record);
      return transaction("readwrite", async (tx) => {
        const receipts = tx.objectStore("legacyImports"),
          store = tx.objectStore("recoveries");
        const id = JSON.stringify([
          value.command.actorId,
          value.command.request.commandId,
        ]);
        const receipt = await request(receipts.get(id));
        if (receipt) {
          if (receipt.legacyPayload !== legacyPayload)
            throw new RecoveryStorageError("conflict");
          return "already-imported";
        }
        const previous = (await request(store.get(value.key))) as
          | RecoveryRecordV2
          | undefined;
        if (previous && !sameCommand(previous, value))
          throw new RecoveryStorageError("conflict");
        if (!previous) await request(store.add(value));
        await request(receipts.add({ id, legacyPayload }));
        return previous ? "already-imported" : "imported";
      });
    },
    acknowledgeLegacyRemoval(actorId, commandId) {
      return transaction("readwrite", async (tx) => {
        await request(
          tx
            .objectStore("legacyImports")
            .delete(JSON.stringify([actorId, commandId])),
        );
      });
    },
  };
}
