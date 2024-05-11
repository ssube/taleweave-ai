import { doesExist } from '@apextoaster/js-utils';
import { Alert, Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material';
import React, { useState } from 'react';
import { useStore } from 'zustand';
import { store, StoreState } from './store';

export interface PlayerPanelProps {
  sendInput: (input: string) => void;
}

export function playerStateSelector(s: StoreState) {
  return {
    character: s.character,
    activeTurn: s.activeTurn,
  };
}

export function PlayerPanel(props: PlayerPanelProps) {
  const state = useStore(store, playerStateSelector);
  const { character, activeTurn } = state;
  const { sendInput } = props;
  const [input, setInput] = useState<string>('');

  if (doesExist(character)) {
    return <Card style={{ minHeight: '6vh', overflow: 'auto' }}>
      <CardContent>
        <Stack direction="column" spacing={2}>
          {activeTurn && <Alert severity="warning">It's your turn!</Alert>}
          <Typography variant="h6">Playing as: {character.name}</Typography>
          <Typography variant="body1">{character.backstory}</Typography>
          <Stack direction="row" spacing={2}>
            <TextField
              fullWidth
              label="Input"
              variant="outlined"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  sendInput(input);
                  setInput('');
                }
              }}
            />
            <Button variant="contained" onClick={() => {
              sendInput(input);
              setInput('');
            }}>Send</Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>;
  }

  return <Card style={{ minHeight: '6vh', overflow: 'auto' }}>
    <CardContent>
      <Typography variant="h6">No player character</Typography>
    </CardContent>
  </Card>;
}
