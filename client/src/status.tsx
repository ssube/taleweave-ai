import { Edit, Save } from '@mui/icons-material';
import { Alert, AlertColor, FormControlLabel, FormGroup, IconButton, Stack, Switch, TextField, Typography } from '@mui/material';
import React from 'react';
import { ReadyState } from 'react-use-websocket';
import { useStore } from 'zustand';
import { StoreState, store } from './store.js';

const statusStrings: Record<ReadyState, string> = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Running',
  [ReadyState.CLOSING]: 'Closing',
  [ReadyState.CLOSED]: 'Closed',
  [ReadyState.UNINSTANTIATED]: 'Unready',
};

const statusColors: Record<ReadyState, AlertColor> = {
  [ReadyState.CONNECTING]: 'info',
  [ReadyState.OPEN]: 'success',
  [ReadyState.CLOSING]: 'warning',
  [ReadyState.CLOSED]: 'warning',
  [ReadyState.UNINSTANTIATED]: 'warning',
};

function download(filename: string, text: string) {
  const element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}

export function statusbarStateSelector(s: StoreState) {
  return {
    autoScroll: s.autoScroll,
    clientName: s.clientName,
    layoutMode: s.layoutMode,
    readyState: s.readyState,
    themeMode: s.themeMode,
    setAutoScroll: s.setAutoScroll,
    setClientName: s.setClientName,
    setLayoutMode: s.setLayoutMode,
    setThemeMode: s.setThemeMode,
    eventHistory: s.eventHistory,
  };
}

export interface StatusbarProps {
  setName: (name: string) => void;
}

export function Statusbar(props: StatusbarProps) {
  const { setName } = props;
  const state = useStore(store, statusbarStateSelector);
  const { autoScroll, clientName, layoutMode, readyState, themeMode, setAutoScroll, setClientName, setLayoutMode, setThemeMode, eventHistory } = state;

  const connectionStatus = statusStrings[readyState as ReadyState];

  return <Alert icon={false} severity={statusColors[readyState as ReadyState]}>
    <Stack direction="row" alignItems="center" gap={4}>
      <Typography>
        Status: {connectionStatus}
      </Typography>
      <FormGroup row>
        <FormControlLabel control={<Switch
          checked={themeMode === 'dark'}
          onChange={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
          inputProps={{ 'aria-label': 'controlled' }}
          sx={{ marginLeft: 'auto' }}
        />} label="Dark Mode" />
        <FormControlLabel control={<Switch
          checked={autoScroll}
          onChange={() => setAutoScroll(autoScroll === false)}
          inputProps={{ 'aria-label': 'controlled' }}
          sx={{ marginLeft: 'auto' }}
        />} label="Auto Scroll" />
        <FormControlLabel control={<Switch
          checked={layoutMode === 'vertical'}
          onChange={() => setLayoutMode(layoutMode === 'vertical' ? 'horizontal' : 'vertical')}
          inputProps={{ 'aria-label': 'controlled' }}
          sx={{ marginLeft: 'auto' }}
        />} label="Vertical Layout" />
      </FormGroup>
      <FormGroup row>
        <TextField
          label="Player Name"
          value={clientName}
          onChange={(e) => setClientName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              setName(clientName);
            }
          }}
          sx={{ marginLeft: 'auto' }}
        />
        <IconButton onClick={() => setName(clientName)}>
          <Edit />
        </IconButton>
      </FormGroup>
      <FormGroup row>
        <FormControlLabel control={<IconButton onClick={() => download('events.json', JSON.stringify(eventHistory, undefined, 2))}>
          <Save />
        </IconButton>} label="Download History" />
      </FormGroup>
    </Stack>
  </Alert>;
}
