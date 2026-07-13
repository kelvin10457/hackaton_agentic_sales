# Decisiones de Diseño para la Demo (Trade-offs)

Este documento justifica las decisiones arquitectónicas y de diseño de la experiencia de usuario (UX) que se tomaron para la demo, las cuales pueden parecer "bugs" en un primer vistazo, pero son características intencionales para cumplir con los **5 Principios de Diseño** del producto.

## 1. Linealidad del Bot ("El bot parece tonto o no responde mis preguntas aleatorias")
Durante las pruebas, los usuarios notaron que el bot no se desvía de sus preguntas del embudo comercial (ej. "¿Con qué monto...?") incluso si se le hace una pregunta financiera válida.

**Justificación Funcional:** 
Esto es **por diseño**. El principio *G1 (No Asesoramiento)* y el principio de *Orientación a la Venta* exigen que el agente no se convierta en un conversador de propósito general (tipo ChatGPT). Su objetivo es **calificar al lead y extraer señales concretas** (monto, horizonte, experiencia, objetivo). Permitir que el usuario desvíe la conversación hacia una clase de economía diluye la tasa de conversión y aumenta el riesgo de que el LLM alucine consejos financieros. El agente "encarrila" al prospecto de vuelta a las preguntas necesarias para el CRM.

## 2. Puntuación "Fría" (Score bajo) ante respuestas incoherentes
Al responder cosas como "eyruieo" a la pregunta "¿En cuánto tiempo te gustaría ver resultados?", el bot continúa pero el usuario termina siendo clasificado como un lead "Frío".

**Justificación Funcional:**
Esto demuestra el funcionamiento correcto del **Parser Determinista (Fase 2)** y el principio *G7 (Cifras Deterministas)*. El LLM no tiene permitido "adivinar" ni interpretar respuestas basura. Si la señal no encaja en el modelo de dominio (ej. un monto claro o un horizonte temporal válido), el extractor arroja `None`. Al no recolectar puntos, la rúbrica del CRM castiga el score y lo manda a la banda "Fría". Esto protege a la empresa de enviar basura comercial al equipo de ventas.

## 3. El bot no pregunta el nombre en el primer mensaje
**Justificación Funcional:**
Aplicación estricta del principio *G4 (Minimización de Datos)* y fricción progresiva. Si pedimos nombre y correo en el saludo, la tasa de rebote (drop-off) es altísima. El flujo está diseñado para enganchar primero con la necesidad del usuario, pedir el nombre orgánicamente (Fase 1), y solo solicitar el correo al final, como moneda de cambio por la entrega de los resultados del Quiz de Perfil de Riesgo.

## 4. Respuestas sobre "Lavar dinero" u otros actos ilícitos
El bot no ofrece respuestas ni se escandaliza dramáticamente; simplemente aplica la **Negativa Honesta**.

**Justificación Funcional:**
El guardrail *G6 (Alcance Temático e Ilícitos)* restringe la superficie de ataque. Responder a inyecciones complejas o preguntas ilegales consume tokens, da lugar a *jailbreaks* y es un riesgo reputacional. Cortar de raíz con un rechazo templado ("Eso no está cubierto...") es el comportamiento estándar B2B.

## 5. Captura única de correo electrónico (Cero redundancia)
Si el usuario rechaza dar el correo o ya lo proporciona, la interfaz se adapta inmediatamente ocultando el recuadro para no molestar más.

**Justificación Funcional:**
Mejora de UX. Se solucionó el "bug" visual donde la UI seguía solicitando el dato. Ahora el estado reacciona dinámicamente y el bot confía en la elección del usuario (G3 - Consentimiento por finalidad). Si no hay correo, no hay entrada al CRM, y el agente se despide cordialmente.
