# Cómo trabajamos en el repositorio (actividades 4.7 y 4.8)

## Ramas

- `main` siempre está desplegable. Nadie hace push directo a `main`.
- Cada historia de usuario se trabaja en una rama: `hu-06-colaboradores`, `fix-fecha-movimiento`.
- Se integra a `main` solo por pull request, con la CI en verde y **una aprobación de otro integrante**.

## Commits

- Mensajes en español, en imperativo y con el código de la historia: `HU-06: permitir invitar colaboradores`.
- Un commit = un cambio con sentido. No mezclar refactor con funcionalidad.

## Revisión cruzada de código (4.7)

Quien revisa verifica, además de que funcione:

1. Que los datos de un negocio nunca se mezclen con los de otro (siempre filtrar por `request.negocio`).
2. Que las vistas que modifican datos tengan `@login_required` y, si corresponde, `@requiere_edicion`.
3. Que haya pruebas para el caso feliz y al menos un caso de error.
4. Que no se suban secretos (`.env`, llaves, contraseñas).

## Antes de abrir el PR

```bash
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Configurar la protección de `main` en GitHub (una vez, lo hace quien administra el repo)

Settings → Branches → Add branch protection rule → `main`:
- Require a pull request before merging → Require approvals: 1
- Require status checks to pass → seleccionar **Pruebas y verificaciones de Django**
