import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import './brand/tokens.css';
import { StorybookSeries } from './website/StorybookSeries';

createRoot(document.getElementById('storybook-series-root')!).render(
  <StrictMode>
    <StorybookSeries />
  </StrictMode>,
);
