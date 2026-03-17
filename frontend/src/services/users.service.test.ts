import api from './api';
import { usersService, rolesService, mapRolToUserRole, mapUserRoleToRolNombre } from './users.service';
import type { Usuario, Rol, CreateUsuarioDto, UpdateUsuarioDto } from './users.service';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Users Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('usersService.getAll', () => {
    const mockUsuarios: Usuario[] = [
      {
        id_empleado: 1,
        nombre: 'Juan',
        apellido: 'Admin',
        usuario: 'jadmin',
        email: '[email protected]',
        telefono: '0981234567',
        direccion: 'Av. Test 123',
        ciudad: 'Asunción',
        pais: 'Paraguay',
        fecha_ingreso: '2024-01-01T00:00:00Z',
        estado: true,
        id_rol: 1,
        rol_nombre: 'Administrador',
      },
      {
        id_empleado: 2,
        nombre: 'María',
        apellido: 'Cajera',
        usuario: 'mcajera',
        email: '[email protected]',
        telefono: '0987654321',
        fecha_ingreso: '2024-02-01T00:00:00Z',
        estado: true,
        id_rol: 3,
        rol_nombre: 'Cajero',
      },
    ];

    test('debe obtener todos los usuarios', async () => {
      mockedApi.get.mockResolvedValue({ data: { results: mockUsuarios } });

      const result = await usersService.getAll();

      expect(mockedApi.get).toHaveBeenCalledWith('/empleados/');
      expect(result).toEqual(mockUsuarios);
      expect(result).toHaveLength(2);
    });

    test('debe manejar respuesta vacía', async () => {
      mockedApi.get.mockResolvedValue({ data: { results: [] } });

      const result = await usersService.getAll();

      expect(result).toEqual([]);
    });

    test('debe manejar error en la petición', async () => {
      const error = new Error('Network error');
      mockedApi.get.mockRejectedValue(error);

      await expect(usersService.getAll()).rejects.toThrow('Network error');
    });
  });

  describe('usersService.getById', () => {
    const mockUsuario: Usuario = {
      id_empleado: 1,
      nombre: 'Juan',
      apellido: 'Admin',
      usuario: 'jadmin',
      email: '[email protected]',
      fecha_ingreso: '2024-01-01T00:00:00Z',
      estado: true,
      id_rol: 1,
      rol_nombre: 'Administrador',
    };

    test('debe obtener usuario por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockUsuario });

      const result = await usersService.getById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/empleados/1/');
      expect(result).toEqual(mockUsuario);
    });

    test('debe manejar error 404', async () => {
      const error = { response: { status: 404 } };
      mockedApi.get.mockRejectedValue(error);

      await expect(usersService.getById(999)).rejects.toEqual(error);
    });
  });

  describe('usersService.create', () => {
    const createData: CreateUsuarioDto = {
      nombre: 'Pedro',
      apellido: 'Gerente',
      usuario: 'pgerente',
      email: '[email protected]',
      password: 'Test1234!',
      telefono: '0981111111',
      direccion: 'Calle Test 456',
      ciudad: 'Asunción',
      pais: 'Paraguay',
      id_rol: 2,
    };

    const mockResponse = {
      success: true,
      empleado: {
        id_empleado: 3,
        ...createData,
        fecha_ingreso: '2024-03-01T00:00:00Z',
        estado: true,
        rol_nombre: 'Gerente',
      },
      mensaje: 'Usuario creado exitosamente',
    };

    test('debe crear un nuevo usuario', async () => {
      mockedApi.post.mockResolvedValue({ data: mockResponse });

      const result = await usersService.create(createData);

      expect(mockedApi.post).toHaveBeenCalledWith('/empleados/', createData);
      expect(result).toEqual(mockResponse.empleado);
      expect(result.id_empleado).toBe(3);
    });

    test('debe manejar error de validación', async () => {
      const error = {
        response: {
          data: {
            success: false,
            mensaje: 'El nombre de usuario ya existe',
          },
        },
      };
      mockedApi.post.mockRejectedValue(error);

      await expect(usersService.create(createData)).rejects.toEqual(error);
    });
  });

  describe('usersService.update', () => {
    const updateData: UpdateUsuarioDto = {
      nombre: 'Juan Actualizado',
      email: '[email protected]',
      telefono: '0981234568',
      id_rol: 2,
    };

    const mockUpdatedUser: Usuario = {
      id_empleado: 1,
      nombre: 'Juan Actualizado',
      apellido: 'Admin',
      usuario: 'jadmin',
      email: '[email protected]',
      telefono: '0981234568',
      fecha_ingreso: '2024-01-01T00:00:00Z',
      estado: true,
      id_rol: 2,
      rol_nombre: 'Gerente',
    };

    test('debe actualizar un usuario existente', async () => {
      mockedApi.patch.mockResolvedValue({ data: mockUpdatedUser });

      const result = await usersService.update(1, updateData);

      expect(mockedApi.patch).toHaveBeenCalledWith('/empleados/1/', updateData);
      expect(result).toEqual(mockUpdatedUser);
    });

    test('debe actualizar parcialmente', async () => {
      const partialUpdate = { telefono: '0981111111' };
      mockedApi.patch.mockResolvedValue({ data: mockUpdatedUser });

      await usersService.update(1, partialUpdate);

      expect(mockedApi.patch).toHaveBeenCalledWith('/empleados/1/', partialUpdate);
    });
  });

  describe('usersService.deactivate', () => {
    const mockDeactivatedUser: Usuario = {
      id_empleado: 1,
      nombre: 'Juan',
      apellido: 'Admin',
      usuario: 'jadmin',
      email: '[email protected]',
      fecha_ingreso: '2024-01-01T00:00:00Z',
      estado: false,
      fecha_baja: '2024-03-01T00:00:00Z',
      id_rol: 1,
      rol_nombre: 'Administrador',
    };

    test('debe desactivar un usuario', async () => {
      mockedApi.patch.mockResolvedValue({ data: mockDeactivatedUser });

      const result = await usersService.deactivate(1);

      expect(mockedApi.patch).toHaveBeenCalledWith('/empleados/1/', {
        estado: false,
        fecha_baja: expect.any(String),
      });
      expect(result.estado).toBe(false);
    });
  });

  describe('usersService.activate', () => {
    const mockActivatedUser: Usuario = {
      id_empleado: 1,
      nombre: 'Juan',
      apellido: 'Admin',
      usuario: 'jadmin',
      email: '[email protected]',
      fecha_ingreso: '2024-01-01T00:00:00Z',
      estado: true,
      fecha_baja: undefined,
      id_rol: 1,
      rol_nombre: 'Administrador',
    };

    test('debe activar un usuario', async () => {
      mockedApi.patch.mockResolvedValue({ data: mockActivatedUser });

      const result = await usersService.activate(1);

      expect(mockedApi.patch).toHaveBeenCalledWith('/empleados/1/', {
        estado: true,
        fecha_baja: null,
      });
      expect(result.estado).toBe(true);
    });
  });

  describe('usersService.changePassword', () => {
    test('debe cambiar la contraseña de un usuario', async () => {
      mockedApi.post.mockResolvedValue({ data: {} });

      await usersService.changePassword(1, { password: 'NewPassword123!' });

      expect(mockedApi.post).toHaveBeenCalledWith('/empleados/1/cambiar_password/', {
        password: 'NewPassword123!',
      });
    });

    test('debe manejar error de contraseña inválida', async () => {
      const error = {
        response: {
          data: {
            mensaje: 'La contraseña no cumple con los requisitos',
          },
        },
      };
      mockedApi.post.mockRejectedValue(error);

      await expect(
        usersService.changePassword(1, { password: '123' })
      ).rejects.toEqual(error);
    });
  });

  describe('usersService.delete', () => {
    test('debe eliminar un usuario', async () => {
      mockedApi.delete.mockResolvedValue({ data: {} });

      await usersService.delete(1);

      expect(mockedApi.delete).toHaveBeenCalledWith('/empleados/1/');
    });
  });
});

describe('Roles Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('rolesService.getAll', () => {
    const mockRoles: Rol[] = [
      {
        id_rol: 1,
        nombre_rol: 'Administrador',
        descripcion: 'Acceso total al sistema',
        estado: true,
      },
      {
        id_rol: 2,
        nombre_rol: 'Gerente',
        descripcion: 'Gestión de operaciones',
        estado: true,
      },
      {
        id_rol: 3,
        nombre_rol: 'Cajero',
        descripcion: 'Operaciones de caja',
        estado: true,
      },
    ];

    test('debe obtener todos los roles', async () => {
      mockedApi.get.mockResolvedValue({ data: { results: mockRoles } });

      const result = await rolesService.getAll();

      expect(mockedApi.get).toHaveBeenCalledWith('/roles/');
      expect(result).toEqual(mockRoles);
      expect(result).toHaveLength(3);
    });
  });

  describe('rolesService.getActive', () => {
    const mockActiveRoles: Rol[] = [
      {
        id_rol: 1,
        nombre_rol: 'Administrador',
        descripcion: 'Acceso total',
        estado: true,
      },
    ];

    test('debe obtener solo roles activos', async () => {
      mockedApi.get.mockResolvedValue({ data: { results: mockActiveRoles } });

      const result = await rolesService.getActive();

      expect(mockedApi.get).toHaveBeenCalledWith('/roles/?estado=true');
      expect(result).toEqual(mockActiveRoles);
    });
  });

  describe('rolesService.getById', () => {
    const mockRol: Rol = {
      id_rol: 1,
      nombre_rol: 'Administrador',
      descripcion: 'Acceso total',
      estado: true,
    };

    test('debe obtener rol por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockRol });

      const result = await rolesService.getById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/roles/1/');
      expect(result).toEqual(mockRol);
    });
  });

  describe('rolesService.create', () => {
    const newRol = {
      nombre_rol: 'Supervisor',
      descripcion: 'Supervisión de operaciones',
      estado: true,
    };

    const mockCreatedRol: Rol = {
      id_rol: 5,
      ...newRol,
    };

    test('debe crear un nuevo rol', async () => {
      mockedApi.post.mockResolvedValue({ data: mockCreatedRol });

      const result = await rolesService.create(newRol);

      expect(mockedApi.post).toHaveBeenCalledWith('/roles/', newRol);
      expect(result).toEqual(mockCreatedRol);
    });
  });

  describe('rolesService.update', () => {
    const updateData = {
      descripcion: 'Nueva descripción',
    };

    const mockUpdatedRol: Rol = {
      id_rol: 1,
      nombre_rol: 'Administrador',
      descripcion: 'Nueva descripción',
      estado: true,
    };

    test('debe actualizar un rol', async () => {
      mockedApi.patch.mockResolvedValue({ data: mockUpdatedRol });

      const result = await rolesService.update(1, updateData);

      expect(mockedApi.patch).toHaveBeenCalledWith('/roles/1/', updateData);
      expect(result).toEqual(mockUpdatedRol);
    });
  });

  describe('rolesService.delete', () => {
    test('debe eliminar un rol', async () => {
      mockedApi.delete.mockResolvedValue({ data: {} });

      await rolesService.delete(1);

      expect(mockedApi.delete).toHaveBeenCalledWith('/roles/1/');
    });
  });
});

describe('Helper Functions', () => {
  describe('mapRolToUserRole', () => {
    test('debe mapear Administrador a admin', () => {
      expect(mapRolToUserRole('Administrador')).toBe('admin');
    });

    test('debe mapear Gerente a gerente', () => {
      expect(mapRolToUserRole('Gerente')).toBe('gerente');
    });

    test('debe mapear Cajero a cajero', () => {
      expect(mapRolToUserRole('Cajero')).toBe('cajero');
    });

    test('debe mapear Empleado a empleado', () => {
      expect(mapRolToUserRole('Empleado')).toBe('empleado');
    });

    test('debe retornar empleado para rol desconocido', () => {
      expect(mapRolToUserRole('Desconocido')).toBe('empleado');
    });
  });

  describe('mapUserRoleToRolNombre', () => {
    test('debe mapear admin a Administrador', () => {
      expect(mapUserRoleToRolNombre('admin')).toBe('Administrador');
    });

    test('debe mapear gerente a Gerente', () => {
      expect(mapUserRoleToRolNombre('gerente')).toBe('Gerente');
    });

    test('debe mapear cajero a Cajero', () => {
      expect(mapUserRoleToRolNombre('cajero')).toBe('Cajero');
    });

    test('debe mapear empleado a Empleado', () => {
      expect(mapUserRoleToRolNombre('empleado')).toBe('Empleado');
    });
  });
});
