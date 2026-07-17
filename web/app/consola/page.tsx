import { ConsolaApp } from '@/components/consola/ConsolaApp';

// La consola vive como componente reutilizable (ConsolaApp): esta ruta la sirve
// a pantalla completa; el landing la monta como overlay (mismo espacio simulado).
export default function ConsolaPage() {
    return <ConsolaApp />;
}
