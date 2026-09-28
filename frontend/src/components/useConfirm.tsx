import { useCallback, useState } from "react";

type ConfirmOptions = {
  confirmLabel?: string;
  // Hide Cancel for messages that only need acknowledging.
  showCancel?: boolean;
  // Optional destructive action shown on the left, e.g. "Delete".
  extraLabel?: string;
};

export type ConfirmChoice =
  | "confirm"
  | "cancel"
  | "extra";

type ConfirmState = {
  message: string;
  options: ConfirmOptions;
  resolve: (choice: ConfirmChoice) => void;
} | null;

export function useConfirm() {
  const [state, setState] = useState<ConfirmState>(null);

  // Resolves with whichever button was pressed.
  const choose = useCallback(
    (message: string, options: ConfirmOptions = {}) => {
      return new Promise<ConfirmChoice>((resolve) => {
        setState({ message, options, resolve });
      });
    },
    [],
  );

  // Resolves true only when the main button was pressed.
  const confirm = useCallback(
    async (message: string, options: ConfirmOptions = {}) =>
      (await choose(message, options)) === "confirm",
    [choose],
  );

  function handleChoice(choice: ConfirmChoice) {
    state?.resolve(choice);
    setState(null);
  }

  const dialog = state && (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <p className="whitespace-pre-line text-slate-800">
          {state.message}
        </p>

        <div className="mt-6 flex items-center justify-between gap-3">
          <div>
            {state.options.extraLabel && (
              <button
                type="button"
                onClick={() => handleChoice("extra")}
                className="rounded-lg border border-slate-300 px-4 py-2 font-semibold text-slate-600 hover:bg-slate-50"
              >
                {state.options.extraLabel}
              </button>
            )}
          </div>

          <div className="flex gap-3">
            {state.options.showCancel !== false && (
              <button
                type="button"
                onClick={() => handleChoice("cancel")}
                className="rounded-lg border border-slate-300 px-4 py-2 font-semibold text-slate-700"
              >
                Cancel
              </button>
            )}

            <button
              type="button"
              onClick={() => handleChoice("confirm")}
              className="rounded-lg bg-cyan-700 px-4 py-2 font-semibold text-white"
            >
              {state.options.confirmLabel ?? "Confirm"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return { choose, confirm, dialog };
}
