'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Import dynamique de Leaflet pour éviter les erreurs SSR
const MapSelector = dynamic(() => import('./map-selector-client'), {
  ssr: false,
  loading: () => <div className="w-full h-[400px] bg-muted animate-pulse rounded-md" />,
});

export default MapSelector;
