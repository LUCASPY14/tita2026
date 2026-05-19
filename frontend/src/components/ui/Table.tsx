import { useState, type ReactNode } from 'react'
import { ChevronLeft, ChevronRight, Inbox } from 'lucide-react'

export interface Column<T> {
  title: string
  dataIndex?: keyof T
  key: string
  width?: number
  render?: (value: unknown, record: T) => ReactNode
}

interface TableProps<T> {
  columns: Column<T>[]
  dataSource: T[]
  rowKey: keyof T | ((record: T) => string | number)
  loading?: boolean
  pageSize?: number
  /** Server-side pagination: controlled page number (1-based) */
  page?: number
  /** Server-side pagination: callback when page changes */
  onPageChange?: (page: number) => void
  /** Server-side pagination: total record count */
  total?: number
}

function getKey<T>(record: T, rowKey: keyof T | ((r: T) => string | number)): string | number {
  return typeof rowKey === 'function' ? rowKey(record) : (record[rowKey] as string | number)
}

export default function Table<T extends object>({
  columns,
  dataSource,
  rowKey,
  loading = false,
  pageSize = 10,
  page: controlledPage,
  onPageChange,
  total: controlledTotal,
}: TableProps<T>) {
  const [internalPage, setInternalPage] = useState(1)

  const isServerSide = controlledPage !== undefined && onPageChange !== undefined
  const page = isServerSide ? controlledPage : internalPage
  const setPage = isServerSide ? onPageChange : setInternalPage
  const total = isServerSide ? (controlledTotal ?? dataSource.length) : dataSource.length

  const totalPages = Math.ceil(total / pageSize)
  const rows = isServerSide ? dataSource : dataSource.slice((page - 1) * pageSize, page * pageSize)

  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap"
                  style={col.width ? { width: col.width } : undefined}
                >
                  {col.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-slate-100 last:border-0">
                  {columns.map((col, j) => (
                    <td key={col.key} className="px-4 py-3.5">
                      <div
                        className="h-3.5 bg-slate-100 rounded-full animate-pulse"
                        style={{ width: `${55 + ((i * 4 + j * 9) % 40)}%` }}
                      />
                    </td>
                  ))}
                </tr>
              ))
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-14 text-center">
                  <div className="flex flex-col items-center gap-2">
                    <Inbox className="w-8 h-8 text-slate-300" />
                    <span className="text-sm text-slate-400">Sin datos</span>
                  </div>
                </td>
              </tr>
            ) : (
              rows.map((record) => (
                <tr
                  key={getKey(record, rowKey)}
                  className="hover:bg-slate-50/80 transition-colors duration-100"
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 whitespace-nowrap text-slate-700">
                      {col.render
                        ? col.render(col.dataIndex ? record[col.dataIndex] : undefined, record)
                        : col.dataIndex
                        ? String(record[col.dataIndex] ?? '')
                        : null}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-slate-500 px-1">
          <span>{total} registros</span>
          <div className="flex items-center gap-1">
            <button
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              const p = totalPages <= 7 ? i + 1
                : page <= 4 ? i + 1
                : page >= totalPages - 3 ? totalPages - 6 + i
                : page - 3 + i
              return p
            }).map((p) => (
              <button
                key={p}
                className={`w-7 h-7 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  p === page
                    ? 'bg-green-600 text-white shadow-sm shadow-green-600/25'
                    : 'border border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
                onClick={() => setPage(p)}
              >
                {p}
              </button>
            ))}
            <button
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
