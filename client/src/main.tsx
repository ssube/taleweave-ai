import { doesExist, mustDefault } from '@apextoaster/js-utils';
import { createRoot } from 'react-dom/client';
import React, { StrictMode } from 'react';

import { App } from './app.js';

export const DEFAULT_SOCKET_PORT = 8001;

export function getSocketProtocol(protocol: string) {
  if (protocol === 'https:') {
    return 'wss:';
  }

  return 'ws:';
}

export function getSocketAddress(protocol: string, hostname: string, port = DEFAULT_SOCKET_PORT) {
  const socketProtocol = getSocketProtocol(protocol);
  return `${socketProtocol}://${hostname}:${port}/`;
}

window.addEventListener('DOMContentLoaded', () => {
  const history = document.querySelector('#history');

  // eslint-disable-next-line no-restricted-syntax
  if (!doesExist(history)) {
    throw new Error('History element not found');
  }

  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const search = new URLSearchParams(window.location.search);
  const socketAddress = mustDefault(search.get('socket'), getSocketAddress(protocol, hostname));

  const root = createRoot(history);
  root.render(<StrictMode><App socketUrl={socketAddress} /></StrictMode>);
});
