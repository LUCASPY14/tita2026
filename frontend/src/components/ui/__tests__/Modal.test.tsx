import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import Modal from '../Modal'

afterEach(() => {
  cleanup()
  document.body.style.overflow = ''
})

describe('Modal', () => {
  it('renders nothing when open is false', () => {
    render(<Modal open={false} title="Test" onCancel={vi.fn()}>Contenido</Modal>)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders the dialog when open is true', () => {
    render(<Modal open title="Test" onCancel={vi.fn()}>Contenido</Modal>)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('shows the title', () => {
    render(<Modal open title="Mi Modal" onCancel={vi.fn()}>Contenido</Modal>)
    expect(screen.getByText('Mi Modal')).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(
      <Modal open title="T" onCancel={vi.fn()}>
        <p>Hola mundo</p>
      </Modal>
    )
    expect(screen.getByText('Hola mundo')).toBeInTheDocument()
  })

  it('has role dialog with aria-modal', () => {
    render(<Modal open title="T" onCancel={vi.fn()}>Body</Modal>)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
  })

  it('sets body overflow to hidden when open', () => {
    render(<Modal open title="T" onCancel={vi.fn()}>Body</Modal>)
    expect(document.body.style.overflow).toBe('hidden')
  })

  it('calls onCancel when Escape key is pressed', () => {
    const onCancel = vi.fn()
    render(<Modal open title="T" onCancel={onCancel}>Body</Modal>)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  it('does not call onCancel on Escape when disableEscape is true', () => {
    const onCancel = vi.fn()
    render(<Modal open title="T" onCancel={onCancel} disableEscape>Body</Modal>)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onCancel).not.toHaveBeenCalled()
  })

  it('does not call onCancel on Escape when confirmLoading is true', () => {
    const onCancel = vi.fn()
    render(<Modal open title="T" onCancel={onCancel} confirmLoading>Body</Modal>)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onCancel).not.toHaveBeenCalled()
  })

  it('calls onCancel when close button (X) is clicked', () => {
    const onCancel = vi.fn()
    render(<Modal open title="T" onCancel={onCancel}>Body</Modal>)
    fireEvent.click(screen.getByLabelText('Cerrar'))
    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  it('calls onCancel when backdrop is clicked', () => {
    const onCancel = vi.fn()
    render(<Modal open title="T" onCancel={onCancel}>Body</Modal>)
    // backdrop is the sibling div before the dialog
    const dialog = screen.getByRole('dialog')
    const backdrop = dialog.previousElementSibling as HTMLElement
    fireEvent.click(backdrop)
    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  it('hides footer when footer prop is null', () => {
    render(<Modal open title="T" onCancel={vi.fn()} footer={null}>Body</Modal>)
    expect(screen.queryByText('Aceptar')).not.toBeInTheDocument()
    expect(screen.queryByText('Cancelar')).not.toBeInTheDocument()
  })

  it('shows default OK/Cancel buttons when footer is undefined', () => {
    render(<Modal open title="T" onCancel={vi.fn()} onOk={vi.fn()}>Body</Modal>)
    expect(screen.getByText('Aceptar')).toBeInTheDocument()
    expect(screen.getByText('Cancelar')).toBeInTheDocument()
  })

  it('calls onOk when OK button is clicked', () => {
    const onOk = vi.fn()
    render(<Modal open title="T" onCancel={vi.fn()} onOk={onOk}>Body</Modal>)
    fireEvent.click(screen.getByText('Aceptar'))
    expect(onOk).toHaveBeenCalledTimes(1)
  })

  it('renders custom footer', () => {
    render(
      <Modal open title="T" onCancel={vi.fn()} footer={<button>Personalizado</button>}>
        Body
      </Modal>
    )
    expect(screen.getByText('Personalizado')).toBeInTheDocument()
    expect(screen.queryByText('Aceptar')).not.toBeInTheDocument()
  })

  it('supports custom okText and cancelText', () => {
    render(
      <Modal open title="T" onCancel={vi.fn()} onOk={vi.fn()} okText="Confirmar" cancelText="Volver">
        Body
      </Modal>
    )
    expect(screen.getByText('Confirmar')).toBeInTheDocument()
    expect(screen.getByText('Volver')).toBeInTheDocument()
  })
})
