import { type SafePlusGuidanceSource } from "../../../api/aiAnalysisApi";
import { getSourceById } from "./resultsHelpers";

export default function SourceLinks({
  sourceIds,
  sources,
}: {
  sourceIds: string[];
  sources: SafePlusGuidanceSource[];
}) {
  if (sourceIds.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        WorkSafe sources
      </p>

      <div className="mt-2 flex flex-wrap gap-2">
        {sourceIds.map((sourceId) => {
          const source = getSourceById(
            sourceId,
            sources,
          );

          if (!source) {
            return (
              <span
                key={sourceId}
                className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600"
              >
                {sourceId}
              </span>
            );
          }

          return (
            <a
              key={sourceId}
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-800 hover:bg-cyan-100"
            >
              {source.title}
            </a>
          );
        })}
      </div>
    </div>
  );
}
