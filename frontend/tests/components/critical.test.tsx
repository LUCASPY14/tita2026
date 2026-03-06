/**
 * Tests críticos de componentes React
 * Smoke tests para componentes más importantes
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Button from '../../src/components/common/Button';
import Input from '../../src/components/common/Input';
import ConfirmDialog from '../../src/components/common/ConfirmDialog';
import EmptyState from '../../src/components/common/EmptyState';
import { Search } from 'lucide-react';

// Helper para envolver componentes con Router
const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('🧪 Critical Components Tests', () => {
  
  describe('Button Component', () => {
    test('✅ CRÍTICO: should render button with text', () => {
      render(<Button>Click Me</Button>);
      expect(screen.getByText('Click Me')).toBeInTheDocument();
    });

    test('✅ CRÍTICO: should handle click events', () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click Me</Button>);
      
      fireEvent.click(screen.getByText('Click Me'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('✅ CRÍTICO: should be disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled Button</Button>);
      const button = screen.getByText('Disabled Button');
      expect(button).toBeDisabled();
    });

    test('✅ CRÍTICO: should apply correct variant styles', () => {
      const { rerender } = render(<Button variant="primary">Primary</Button>);
      expect(screen.getByText('Primary')).toHaveClass('bg-blue-600');

      rerender(<Button variant="danger">Danger</Button>);
      expect(screen.getByText('Danger')).toHaveClass('bg-red-600');
    });
  });

  describe('Input Component', () => {
    test('✅ CRÍTICO: should render input with label', () => {
      render(<Input label="Username" />);
      expect(screen.getByText('Username')).toBeInTheDocument();
    });

    test('✅ CRÍTICO: should handle value changes', () => {
      const handleChange = jest.fn();
      render(<Input onChange={handleChange} />);
      
      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'test value' } });
      
      expect(handleChange).toHaveBeenCalled();
    });

    test('✅ CRÍTICO: should show error message when error prop is provided', () => {
      render(<Input error="This field is required" />);
      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });

    test('✅ CRÍTICO: should be disabled when disabled prop is true', () => {
      render(<Input disabled />);
      expect(screen.getByRole('textbox')).toBeDisabled();
    });
  });

  describe('ConfirmDialog Component', () => {
    test('✅ CRÍTICO: should render when isOpen is true', () => {
      render(
        <ConfirmDialog
          isOpen={true}
          onClose={() => {}}
          onConfirm={() => {}}
          title="Confirm Action"
          message="Are you sure?"
        />
      );
      
      expect(screen.getByText('Confirm Action')).toBeInTheDocument();
      expect(screen.getByText('Are you sure?')).toBeInTheDocument();
    });

    test('✅ CRÍTICO: should not render when isOpen is false', () => {
      const { container } = render(
        <ConfirmDialog
          isOpen={false}
          onClose={() => {}}
          onConfirm={() => {}}
          title="Confirm Action"
          message="Are you sure?"
        />
      );
      
      expect(container.firstChild).toBeNull();
    });

    test('✅ CRÍTICO: should call onConfirm when confirm button is clicked', async () => {
      const handleConfirm = jest.fn();
      render(
        <ConfirmDialog
          isOpen={true}
          onClose={() => {}}
          onConfirm={handleConfirm}
          title="Confirm Action"
          message="Are you sure?"
        />
      );
      
      const confirmButton = screen.getByText('Confirmar');
      fireEvent.click(confirmButton);
      
      await waitFor(() => {
        expect(handleConfirm).toHaveBeenCalledTimes(1);
      });
    });

    test('✅ CRÍTICO: should call onClose when cancel button is clicked', () => {
      const handleClose = jest.fn();
      render(
        <ConfirmDialog
          isOpen={true}
          onClose={handleClose}
          onConfirm={() => {}}
          title="Confirm Action"
          message="Are you sure?"
        />
      );
      
      const cancelButton = screen.getByText('Cancelar');
      fireEvent.click(cancelButton);
      
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('EmptyState Component', () => {
    test('✅ CRÍTICO: should render with icon and title', () => {
      render(
        <EmptyState
          icon={Search}
          title="No results found"
        />
      );
      
      expect(screen.getByText('No results found')).toBeInTheDocument();
    });

    test('✅ CRÍTICO: should render description when provided', () => {
      render(
        <EmptyState
          icon={Search}
          title="No results"
          description="Try adjusting your search filters"
        />
      );
      
      expect(screen.getByText('Try adjusting your search filters')).toBeInTheDocument();
    });

    test('✅ CRÍTICO: should render action button when provided', () => {
      const handleAction = jest.fn();
      render(
        <EmptyState
          icon={Search}
          title="No results"
          action={{
            label: 'Clear filters',
            onClick: handleAction
          }}
        />
      );
      
      const actionButton = screen.getByText('Clear filters');
      expect(actionButton).toBeInTheDocument();
      
      fireEvent.click(actionButton);
      expect(handleAction).toHaveBeenCalledTimes(1);
    });

    test('✅ CRÍTICO: should apply correct size classes', () => {
      const { rerender, container } = render(
        <EmptyState icon={Search} title="Test" size="sm" />
      );
      
      // Check for small size class
      expect(container.querySelector('.h-8')).toBeInTheDocument();
      
      rerender(<EmptyState icon={Search} title="Test" size="lg" />);
      
      // Check for large size class
      expect(container.querySelector('.h-16')).toBeInTheDocument();
    });
  });
});
