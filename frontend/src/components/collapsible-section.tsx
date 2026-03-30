import type { ReactNode } from "react";

export function Section({
  title,
  icon,
  count,
  editing,
  onToggleEdit,
  onAdd,
  children,
}: {
  title: string;
  icon: ReactNode;
  count?: number;
  editing?: boolean;
  onToggleEdit?: () => void;
  onAdd?: () => void;
  children: ReactNode;
}) {
  return (
    <div className={`bg-white dark:bg-slate-900 border rounded-xl p-4 transition-colors ${editing ? "border-blue-500/50" : "border-slate-200 dark:border-slate-700"}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
            {title}
          </span>
          {count !== undefined && (
            <span className="text-xs text-slate-400">({count})</span>
          )}
        </div>
        {onToggleEdit && (
          <button
            onClick={onToggleEdit}
            className={`text-xs cursor-pointer transition-colors ${editing ? "text-blue-500 font-medium" : "text-slate-400 hover:text-blue-500"}`}
          >
            {editing ? "完成" : "編輯"}
          </button>
        )}
      </div>
      <div className="divide-y divide-slate-100 dark:divide-slate-800">
        {children}
      </div>
      {editing && onAdd && (
        <button
          onClick={onAdd}
          className="mt-3 w-full py-2 text-xs text-blue-500 border border-dashed border-blue-500/30 rounded-lg hover:bg-blue-500/5 cursor-pointer transition-colors"
        >
          + 新增
        </button>
      )}
    </div>
  );
}
