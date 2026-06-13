import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import Table, { type Column } from '../Table'

// ─── fixtures ─────────────────────────────────────────────────────────────────

type Row = { id: number; nombre: string; monto: number }

const COLUMNS: Column<Row>[] = [
  { title: 'ID', dataIndex: 'id', key: 'id' },
  { title: 'Nombre', dataIndex: 'nombre', key: 'nombre' },
  { title: 'Monto', dataIndex: 'monto', key: 'monto' },
]

function makeRows(count: number): Row[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    nombre: `Item ${i + 1}`,
    monto: (i + 1) * 1000,
  }))
}

// ─── render básico ────────────────────────────────────────────────────────────

describe('Table — render', () => {
  it('muestra los encabezados de columna', () => {
    render(<Table columns={COLUMNS} dataSource={[]} rowKey="id" />)
    expect(screen.getByRole('columnheader', { name: 'ID' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Nombre' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Monto' })).toBeInTheDocument()
  })

  it('renderiza las filas de datos', () => {
    render(<Table columns={COLUMNS} dataSource={makeRows(3)} rowKey="id" />)
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
    expect(screen.getByText('Item 3')).toBeInTheDocument()
  })

  it('muestra "Sin datos" cuando dataSource está vacío', () => {
    render(<Table columns={COLUMNS} dataSource={[]} rowKey="id" />)
    expect(screen.getByText('Sin datos')).toBeInTheDocument()
  })

  it('muestra filas skeleton cuando loading=true', () => {
    const { container } = render(
      <Table columns={COLUMNS} dataSource={[]} rowKey="id" loading />,
    )
    const skeletons = container.querySelectorAll('.animate-pulse')
    // 5 filas × 3 columnas = 15 elementos skeleton
    expect(skeletons.length).toBe(15)
  })
})

// ─── render personalizado ─────────────────────────────────────────────────────

describe('Table — render function', () => {
  it('usa la función render() cuando se provee en la columna', () => {
    const columnsConRender: Column<Row>[] = [
      ...COLUMNS,
      {
        title: 'Acción',
        key: 'accion',
        render: (_, record) => <button>Editar {record.nombre}</button>,
      },
    ]
    render(<Table columns={columnsConRender} dataSource={makeRows(1)} rowKey="id" />)
    expect(screen.getByRole('button', { name: 'Editar Item 1' })).toBeInTheDocument()
  })
})

// ─── paginación client-side ───────────────────────────────────────────────────

describe('Table — paginación client-side', () => {
  it('muestra solo pageSize filas en la primera página', () => {
    render(<Table columns={COLUMNS} dataSource={makeRows(25)} rowKey="id" pageSize={10} />)
    // Solo los primeros 10 items deben estar visibles
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 10')).toBeInTheDocument()
    expect(screen.queryByText('Item 11')).not.toBeInTheDocument()
  })

  it('navega a la página siguiente al hacer click en "Página siguiente"', async () => {
    render(<Table columns={COLUMNS} dataSource={makeRows(25)} rowKey="id" pageSize={10} />)
    await userEvent.click(screen.getByRole('button', { name: /página siguiente/i }))
    expect(screen.getByText('Item 11')).toBeInTheDocument()
    expect(screen.queryByText('Item 1')).not.toBeInTheDocument()
  })

  it('el botón "Página anterior" está deshabilitado en la primera página', () => {
    render(<Table columns={COLUMNS} dataSource={makeRows(25)} rowKey="id" pageSize={10} />)
    expect(screen.getByRole('button', { name: /página anterior/i })).toBeDisabled()
  })

  it('el botón "Página siguiente" está deshabilitado en la última página', async () => {
    render(<Table columns={COLUMNS} dataSource={makeRows(20)} rowKey="id" pageSize={10} />)
    await userEvent.click(screen.getByRole('button', { name: /página siguiente/i }))
    expect(screen.getByRole('button', { name: /página siguiente/i })).toBeDisabled()
  })

  it('no muestra paginación cuando los datos caben en una sola página', () => {
    render(<Table columns={COLUMNS} dataSource={makeRows(5)} rowKey="id" pageSize={10} />)
    expect(screen.queryByRole('button', { name: /página siguiente/i })).not.toBeInTheDocument()
  })
})

// ─── ordenamiento ─────────────────────────────────────────────────────────────

describe('Table — columnas ordenables', () => {
  it('muestra botón de sort en columnas con sortable=true', () => {
    const cols: Column<Row>[] = [
      { title: 'Nombre', dataIndex: 'nombre', key: 'nombre', sortable: true },
    ]
    render(<Table columns={cols} dataSource={makeRows(2)} rowKey="id" />)
    expect(screen.getByRole('button', { name: /ordenar por nombre/i })).toBeInTheDocument()
  })

  it('llama a onSort con "asc" en el primer click', async () => {
    const onSort = vi.fn()
    const cols: Column<Row>[] = [
      { title: 'Nombre', dataIndex: 'nombre', key: 'nombre', sortable: true },
    ]
    render(
      <Table columns={cols} dataSource={makeRows(2)} rowKey="id" onSort={onSort} />,
    )
    await userEvent.click(screen.getByRole('button', { name: /ordenar por nombre/i }))
    expect(onSort).toHaveBeenCalledWith('nombre', 'asc')
  })

  it('alterna a "desc" cuando ya está ordenado "asc" por esa columna', async () => {
    const onSort = vi.fn()
    const cols: Column<Row>[] = [
      { title: 'Nombre', dataIndex: 'nombre', key: 'nombre', sortable: true },
    ]
    render(
      <Table
        columns={cols}
        dataSource={makeRows(2)}
        rowKey="id"
        sortKey="nombre"
        sortDir="asc"
        onSort={onSort}
      />,
    )
    await userEvent.click(screen.getByRole('button', { name: /ordenar por nombre/i }))
    expect(onSort).toHaveBeenCalledWith('nombre', 'desc')
  })
})

// ─── paginación server-side ───────────────────────────────────────────────────

describe('Table — paginación server-side', () => {
  it('muestra el total de registros del servidor', () => {
    render(
      <Table
        columns={COLUMNS}
        dataSource={makeRows(10)}
        rowKey="id"
        page={1}
        onPageChange={vi.fn()}
        total={100}
        pageSize={10}
      />,
    )
    expect(screen.getByText('100 registros')).toBeInTheDocument()
  })

  it('llama a onPageChange cuando el usuario hace click en la siguiente página', async () => {
    const onPageChange = vi.fn()
    render(
      <Table
        columns={COLUMNS}
        dataSource={makeRows(10)}
        rowKey="id"
        page={1}
        onPageChange={onPageChange}
        total={50}
        pageSize={10}
      />,
    )
    await userEvent.click(screen.getByRole('button', { name: /página siguiente/i }))
    expect(onPageChange).toHaveBeenCalledWith(2)
  })
})
