import axios from "axios";

/** The protected request was withheld because the current session could not be checked. */
export class SessionNotConfirmedError extends axios.CanceledError<unknown> {}
