import { doesExist } from '@apextoaster/js-utils';
import { createRoot } from 'react-dom/client';
import React, { StrictMode } from 'react';

import { App } from './app.js';

window.addEventListener('DOMContentLoaded', () => {
  const history = document.querySelector('#history');

  // eslint-disable-next-line no-restricted-syntax
  if (!doesExist(history)) {
    throw new Error('History element not found');
  }

  const hostname = window.location.hostname;
  const root = createRoot(history);
  root.render(<StrictMode><App socketUrl={`ws://${hostname}:8001/`} /></StrictMode>);
});
