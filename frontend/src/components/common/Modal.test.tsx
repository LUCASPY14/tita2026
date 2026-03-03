/**
 * Tests para el componente Modal
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Modal from './Modal';

describe('Modal Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  test('no renderiza cuando isOpen=false', () => {
    const { container } = render(
      <Modal isOpen={false} onClose={mockOnClose}>
        <p>Modal Content</p>
      </Modal>
    );
    expect(screen.queryByText('Modal Content')).not.toBeInTheDocument();
  });

  test('renderiza cuando isOpen=true', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <p>Modal Content</p>
      </Modal>
    );
    expect(screen.getByText('Modal Content')).toBeInTheDocument();
  });

  test('muestra título cuando se proporciona', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
        <p>Content</p>
      </Modal>
    );
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  test('muestra subtítulo cuando se proporciona', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} subtitle="Modal Description">
        <p>Content</p>
      </Modal>
    );
    expect(screen.getByText('Modal Description')).toBeInTheDocument();
  });

  test('muestra botón cerrar por defecto', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Test">
        <p>Content</p>
      </Modal>
    );
    const closeButton = screen.getByRole('button');
    expect(closeButton).toBeInTheDocument();
  });

  test('no muestra botón cerrar cuando showCloseButton=false', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} showCloseButton={false}>
        <p>Content</p>
      </Modal>
    );
    const closeButton = screen.queryByRole('button');
    expect(closeButton).not.toBeInTheDocument();
  });

  test('llama onClose cuando se hace click en botón cerrar', async () => {
    const user = userEvent.setup();
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Test">
        <p>Content</p>
      </Modal>
    );
    const closeButton = screen.getByRole('button');
    await user.click(closeButton);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  test('renderiza footer cuando se proporciona', () => {
    render(
      <Modal 
        isOpen={true} 
        onClose={mockOnClose}
        footer={<button>Save</button>}
      >
        <p>Content</p>
      </Modal>
    );
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  test('renderiza children correctamente', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div>
          <h2>Custom Content</h2>
          <p>Some text</p>
        </div>
      </Modal>
    );
    expect(screen.getByText('Custom Content')).toBeInTheDocument();
    expect(screen.getByText('Some text')).toBeInTheDocument();
  });
});
