/**
 * Tests para el componente FormFields
 */
import { render, screen } from '@testing-library/react';
import { 
  FormInput, 
  FormSelect, 
  FormCheckbox, 
  FormTextarea, 
  FormGroup 
} from './FormFields';

describe('FormFields Components', () => {
  describe('FormInput', () => {
    test('renderiza FormInput correctamente', () => {
      render(<FormInput name="username" label="Usuario" />);
      expect(screen.getByLabelText('Usuario')).toBeInTheDocument();
    });

    test('pasa props al componente Input', () => {
      render(<FormInput name="email" type="email" placeholder="Correo" />);
      const input = screen.getByPlaceholderText('Correo');
      expect(input).toHaveAttribute('type', 'email');
    });
  });

  describe('FormSelect', () => {
    const options = [
      { value: '1', label: 'Opción 1' },
      { value: '2', label: 'Opción 2' },
    ];

    test('renderiza FormSelect correctamente', () => {
      render(<FormSelect name="category" label="Categoría" options={options} />);
      expect(screen.getByLabelText('Categoría')).toBeInTheDocument();
    });

    test('pasa props al componente Select', () => {
      render(<FormSelect name="test" options={options} />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('FormCheckbox', () => {
    test('renderiza FormCheckbox correctamente', () => {
      render(<FormCheckbox name="terms" label="Acepto términos" />);
      expect(screen.getByLabelText('Acepto términos')).toBeInTheDocument();
    });

    test('pasa props al componente Checkbox', () => {
      render(<FormCheckbox name="test" defaultChecked />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeChecked();
    });
  });

  describe('FormTextarea', () => {
    test('renderiza FormTextarea correctamente', () => {
      render(<FormTextarea name="description" label="Descripción" />);
      expect(screen.getByLabelText('Descripción')).toBeInTheDocument();
    });

    test('pasa props al componente Textarea', () => {
      render(<FormTextarea name="test" rows={10} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('rows', '10');
    });
  });

  describe('FormGroup', () => {
    test('renderiza FormGroup correctamente', () => {
      render(
        <FormGroup label="Datos personales">
          <p>Contenido del grupo</p>
        </FormGroup>
      );
      expect(screen.getByText('Datos personales')).toBeInTheDocument();
      expect(screen.getByText('Contenido del grupo')).toBeInTheDocument();
    });

    test('muestra asterisco cuando required=true', () => {
      render(
        <FormGroup label="Requerido" required>
          <p>Content</p>
        </FormGroup>
      );
      const asterisk = screen.getByText('*');
      expect(asterisk).toBeInTheDocument();
      expect(asterisk).toHaveClass('text-red-500');
    });

    test('muestra mensaje de error cuando se proporciona', () => {
      render(
        <FormGroup error="Error en el grupo">
          <p>Content</p>
        </FormGroup>
      );
      expect(screen.getByText('Error en el grupo')).toBeInTheDocument();
    });

    test('muestra helper text cuando se proporciona', () => {
      render(
        <FormGroup helperText="Texto de ayuda">
          <p>Content</p>
        </FormGroup>
      );
      expect(screen.getByText('Texto de ayuda')).toBeInTheDocument();
    });

    test('no muestra helper text cuando hay error', () => {
      render(
        <FormGroup error="Error" helperText="Ayuda">
          <p>Content</p>
        </FormGroup>
      );
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.queryByText('Ayuda')).not.toBeInTheDocument();
    });

    test('aplica className personalizado', () => {
      const { container } = render(
        <FormGroup className="custom-class">
          <p>Content</p>
        </FormGroup>
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });

    test('renderiza múltiples children', () => {
      render(
        <FormGroup>
          <input name="field1" />
          <input name="field2" />
          <input name="field3" />
        </FormGroup>
      );
      const inputs = screen.getAllByRole('textbox');
      expect(inputs).toHaveLength(3);
    });
  });
});
