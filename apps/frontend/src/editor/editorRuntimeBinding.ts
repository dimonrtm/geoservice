import { getActivePinia, type Pinia } from "pinia";
import type { EditorWorkflow } from "./createEditorWorkflow";
import type { EditorWorkflowPorts } from "./editorWorkflowPorts";
export interface EditorRuntime {
  workflow: EditorWorkflow;
  sessionAccess: {
    readonly actorId: string | null;
    readonly isAuthenticated: boolean;
    readonly canEdit: boolean;
    readonly sessionEpoch: number;
    logout(): Promise<boolean>;
  };
  dispose(): void;
}

const runtimes = new WeakMap<Pinia, EditorRuntime>();
export function findEditorRuntime(pinia: Pinia): EditorRuntime | undefined {
  return runtimes.get(pinia);
}
export function bindEditorRuntime(
  pinia: Pinia,
  runtime: EditorRuntime,
): () => void {
  runtimes.set(pinia, runtime);
  return () => runtimes.delete(pinia);
}
export function getEditorRuntime(
  pinia: Pinia | undefined = getActivePinia(),
): EditorRuntime {
  const runtime = pinia && findEditorRuntime(pinia);
  if (!runtime) throw new Error("Editor runtime must be installed before use");
  return runtime;
}

const bindings = new WeakMap<object, EditorWorkflow>();
// Pinia devtools supplies a fresh Proxy as an action's `this`. Its $state
// remains the owner's stable identity, including across ordinary $reset.
function bindingKey(owner: object): object {
  return "$state" in owner &&
    owner.$state !== null &&
    typeof owner.$state === "object"
    ? owner.$state
    : owner;
}
const dependencies = new WeakMap<
  object,
  Pick<
    EditorWorkflowPorts,
    "editVersionCommands" | "editVersionDraft" | "editorNavigation"
  > & {
    auth: Pick<
      EditorWorkflowPorts["auth"],
      "user" | "isAuthenticated" | "sessionEpoch"
    >;
  }
>();
export function bindEditorDependencies(
  owner: object,
  ports: EditorWorkflowPorts,
): () => void {
  const key = bindingKey(owner);
  dependencies.set(key, ports);
  return () => {
    dependencies.delete(key);
  };
}
export function editorDependencies(owner: object) {
  const ports = dependencies.get(bindingKey(owner));
  if (!ports)
    throw new Error("Editor runtime must be installed before session actions");
  return ports;
}
export function bindEditorWorkflow(
  owner: object,
  workflow: EditorWorkflow,
): () => void {
  const key = bindingKey(owner);
  bindings.set(key, workflow);
  return () => {
    if (bindings.get(key) === workflow) bindings.delete(key);
  };
}
export function requireEditorWorkflow(owner: object): EditorWorkflow {
  const workflow = bindings.get(bindingKey(owner));
  if (!workflow)
    throw new Error("Editor runtime must be installed before editor actions");
  return workflow;
}
