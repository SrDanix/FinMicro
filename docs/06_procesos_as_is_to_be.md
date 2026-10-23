# Modelamiento de procesos

**Actividades 3.1 (AS-IS) y 3.2 (TO-BE)** · Responsable: Marcelo · Aprueba: Carlos · Semanas 5–6

> El AS-IS se construyó a partir del perfil del microempresario informal descrito en el
> informe. **Debe contrastarse con los resultados de las entrevistas (actividad 2.5)**:
> si el trabajo de campo muestra otro flujo, se ajusta este diagrama y la pila de producto.

## 3.1 Proceso actual (AS-IS): control financiero de un microempresario informal

```mermaid
flowchart TD
    A([Fin del día de venta]) --> B[Cuenta el efectivo y revisa transferencias en la app del banco]
    B --> C{¿Anota las ventas?}
    C -- A veces --> D[Anota en cuaderno o en notas del celular]
    C -- No --> E[Confía en la memoria]
    D --> F[Compra mercadería con lo que hay en caja]
    E --> F
    F --> G{¿Guarda las boletas de compra?}
    G -- Pocas veces --> H[Bolsa o caja con papeles]
    G -- No --> I[Se pierden]
    H --> J([Fin de mes])
    I --> J
    J --> K{¿Sabe si ganó o perdió?}
    K -- Aproximadamente --> L[Estima por el saldo de la cuenta]
    K -- No --> L
    L --> M{¿Tiene obligaciones con el SII?}
    M -- Sí --> N[Busca a un contador o pregunta a conocidos]
    M -- No sabe --> O[No declara]
    N --> P[Arma el F29 con datos incompletos, a veces fuera de plazo]
```

**Problemas observados**

| # | Problema | Consecuencia |
|---|---|---|
| P1 | Registro irregular de ventas y gastos | No conoce su utilidad real |
| P2 | Mezcla de dinero personal y del negocio | Decisiones de compra sin información |
| P3 | Respaldos de compras perdidos | Pierde crédito fiscal de IVA |
| P4 | Desconocimiento de tasas y plazos | Multas, intereses o informalidad por temor |
| P5 | Dependencia de un tercero para cualquier cálculo | Costo y demora |
| P6 | Sin proyección | No sabe si puede invertir o endeudarse |

## 3.2 Proceso propuesto (TO-BE): con FinMicro

```mermaid
flowchart TD
    A([Durante o al fin del día]) --> B[Registra la venta o el gasto en FinMicro desde el celular]
    B --> C[FinMicro clasifica por categoría y suma al mes]
    C --> D[Panel: balance, gráfico y avance de la meta]
    D --> E{¿Se acerca a un vencimiento o al límite del plan?}
    E -- Sí --> F[Alerta en el panel]
    E -- No --> G([Sigue operando])
    F --> G
    G --> H([Fin de mes])
    H --> I[Calculadora de IVA / honorarios con datos del mes]
    I --> J{¿Necesita ayuda profesional?}
    J -- Sí --> K[Invita a su contador como colaborador de solo lectura]
    J -- No --> L[Declara en sii.cl con las cifras de FinMicro]
    K --> L
    L --> M[Proyección de ingresos y evaluador de viabilidad para decidir inversiones]
```

**Cómo responde el TO-BE a cada problema**

| Problema | Respuesta | RF |
|---|---|---|
| P1 | Registro en menos de un minuto, desde el celular | RF-08, RNF-10, RNF-11 |
| P2 | El panel muestra solo los movimientos del negocio | RF-14, RF-33 |
| P3 | Categorías marcadas como afectas a IVA; importación de compras | RF-09, RF-12, RF-22 |
| P4 | Calculadoras con tasas vigentes y calendario de vencimientos | RF-20, RF-21, RF-23 |
| P5 | El contador entra como colaborador, sin compartir claves | RF-06 |
| P6 | Proyección de ingresos y VAN/TIR | RF-34, RF-35 |
