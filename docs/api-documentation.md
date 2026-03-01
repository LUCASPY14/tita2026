# API Reference

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.cantina-tita.com/api/v1
```

## Autenticación

### Login
```http
POST /auth/login/
Content-Type: application/json

{
  "username": "usuario",
  "password": "contraseña"
}

Response:
{
  "token": "eyJ0eXAiOiJKV1...",
  "user": {
    "id": 1,
    "username": "usuario",
    "email": "usuario@example.com",
    "role": "ADMIN"
  }
}
```

### Headers
Todas las peticiones autenticadas deben incluir:
```
Authorization: Bearer {token}
```

## Endpoints

### Clientes

#### Listar Clientes
```http
GET /clientes/
Query Parameters:
  - page: número de página (default: 1)
  - page_size: tamaño de página (default: 10)
  - search: búsqueda por nombre o RUC

Response:
{
  "count": 100,
  "next": "http://api.../clientes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "nombre": "Juan Pérez",
      "ruc": "12345678-9",
      "telefono": "0981234567",
      "email": "juan@example.com",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### Crear Cliente
```http
POST /clientes/
Content-Type: application/json

{
  "nombre": "Juan Pérez",
  "ruc": "12345678-9",
  "telefono": "0981234567",
  "email": "juan@example.com",
  "direccion": "Asunción, Paraguay"
}

Response: 201 Created
{
  "id": 1,
  "nombre": "Juan Pérez",
  ...
}
```

#### Actualizar Cliente
```http
PUT /clientes/{id}/
PATCH /clientes/{id}/
Content-Type: application/json

{
  "telefono": "0987654321"
}

Response: 200 OK
```

#### Eliminar Cliente
```http
DELETE /clientes/{id}/

Response: 204 No Content
```

### Ventas

#### Listar Ventas
```http
GET /ventas/
Query Parameters:
  - fecha_desde: YYYY-MM-DD
  - fecha_hasta: YYYY-MM-DD
  - estado: PENDIENTE|COMPLETADA|CANCELADA
  - cliente_id: ID del cliente

Response:
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "numero": "V-0001",
      "fecha": "2024-01-01T10:00:00Z",
      "cliente": {
        "id": 1,
        "nombre": "Juan Pérez"
      },
      "total": 150000,
      "estado": "COMPLETADA",
      "metodo_pago": "EFECTIVO",
      "items": [
        {
          "producto": "Producto 1",
          "cantidad": 2,
          "precio_unitario": 50000,
          "subtotal": 100000
        }
      ]
    }
  ]
}
```

#### Crear Venta
```http
POST /ventas/
Content-Type: application/json

{
  "cliente_id": 1,
  "metodo_pago": "EFECTIVO",
  "items": [
    {
      "producto_id": 1,
      "cantidad": 2,
      "precio_unitario": 50000
    }
  ]
}

Response: 201 Created
```

#### Cancelar Venta
```http
POST /ventas/{id}/cancelar/

Response: 200 OK
{
  "id": 1,
  "estado": "CANCELADA",
  "mensaje": "Venta cancelada exitosamente"
}
```

### Productos

#### Listar Productos
```http
GET /productos/
Query Parameters:
  - categoria: ID de categoría
  - en_stock: true|false
  - search: búsqueda por nombre o código

Response:
{
  "count": 30,
  "results": [
    {
      "id": 1,
      "codigo": "PROD-001",
      "nombre": "Producto 1",
      "descripcion": "Descripción del producto",
      "precio": 50000,
      "stock": 100,
      "categoria": {
        "id": 1,
        "nombre": "Categoría 1"
      }
    }
  ]
}
```

#### Crear Producto
```http
POST /productos/
Content-Type: application/json

{
  "codigo": "PROD-001",
  "nombre": "Producto 1",
  "descripcion": "Descripción",
  "precio": 50000,
  "stock": 100,
  "categoria_id": 1,
  "stock_minimo": 10
}

Response: 201 Created
```

### Almuerzos

#### Registrar Consumo Diario
```http
POST /almuerzos/consumo/
Content-Type: application/json

{
  "fecha": "2024-01-01",
  "hijo_id": 1,
  "plan_id": 1
}

Response: 201 Created
```

#### Obtener Cuenta Mensual
```http
GET /almuerzos/cuenta-mensual/{cliente_id}/
Query Parameters:
  - mes: 1-12
  - año: YYYY

Response:
{
  "cliente": {
    "id": 1,
    "nombre": "Juan Pérez"
  },
  "mes": 1,
  "año": 2024,
  "hijos": [
    {
      "nombre": "Hijo 1",
      "dias_consumidos": 20,
      "plan": "Plan Mensual",
      "precio_unitario": 15000,
      "total": 300000
    }
  ],
  "total_general": 300000
}
```

### Reportes

#### Reporte de Ventas
```http
GET /reportes/ventas/
Query Parameters:
  - fecha_desde: YYYY-MM-DD
  - fecha_hasta: YYYY-MM-DD
  - agrupado_por: dia|semana|mes

Response:
{
  "periodo": {
    "desde": "2024-01-01",
    "hasta": "2024-01-31"
  },
  "total_ventas": 5000000,
  "cantidad_ventas": 150,
  "promedio_venta": 33333,
  "ventas_por_dia": [
    {
      "fecha": "2024-01-01",
      "total": 150000,
      "cantidad": 5
    }
  ]
}
```

## Códigos de Estado

- `200 OK`: Petición exitosa
- `201 Created`: Recurso creado
- `204 No Content`: Eliminación exitosa
- `400 Bad Request`: Error en los datos enviados
- `401 Unauthorized`: No autenticado
- `403 Forbidden`: Sin permisos
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## Paginación

Todas las listas están paginadas por defecto con 10 items por página.

```
?page=2&page_size=20
```

## Filtrado y Búsqueda

Usar el parámetro `search` para búsqueda de texto:
```
?search=juan
```

Usar filtros específicos para cada campo:
```
?estado=COMPLETADA&fecha_desde=2024-01-01
```

## Ordenamiento

Usar el parámetro `ordering`:
```
?ordering=-fecha (descendente)
?ordering=nombre (ascendente)
```
