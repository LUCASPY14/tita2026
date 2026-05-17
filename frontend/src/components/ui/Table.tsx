import { useState, type ReactNode } from 'react'

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
}: TableProps<T>) {
  const [page, setPage] = useState(1)
  const total = dataSource.length
  const totalPages = Math.ceil(total / pageSize)
  const start = (page - 1) * pageSize
  const rows = dataSource.slice(start, start + pageSize)

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-3 font-medium whitespace-nowrap"
                  style={col.width ? { width: col.width } : undefined}
                >
                  {col.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3">
                      <div className="h-4 bg-gray-200 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-gray-400">
                  Sin datos
                </td>
              </tr>
            ) : (
              rows.map((record) => (
                <tr key={getKey(record, rowKey)} className="hover:bg-gray-50">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 whitespace-nowrap">
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
        <div className="flex items-center justify-between mt-3 text-sm text-gray-600">
          <span>{total} registros</span>
          <div className="flex gap-1">
            <button
              className="px-3 py-1 border rounded disabled:opacity-40"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              &lt;
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                className={`px-3 py-1 border rounded ${p === page ? 'bg-green-600 text-white border-green-600' : 'hover:bg-gray-50'}`}
                onClick={() => setPage(p)}
              >
                {p}
              </button>
            ))}
            <button
              className="px-3 py-1 border rounded disabled:opacity-40"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              &gt;
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
