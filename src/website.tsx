import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import './brand/tokens.css';
import { CanvasStudioWebsite } from './website/CanvasStudioWebsite';

createRoot(document.getElementById('website-root')!).render(
  <StrictMode>
    <CanvasStudioWebsite />
  </StrictMode>,
);
