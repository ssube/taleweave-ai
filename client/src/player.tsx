import React, { useState } from 'react';
import { Maybe } from '@apextoaster/js-utils';
import { Alert, Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material';
import { Actor, SetDetails } from './world.js';

export interface PlayerPanelProps {
  actor: Maybe<Actor>;
  activeTurn: boolean;
  setDetails: SetDetails;
  sendInput: (input: string) => void;
}

export function PlayerPanel(props: PlayerPanelProps) {
  const { actor, activeTurn, sendInput } = props;
  const [input, setInput] = useState<string>('');

  // eslint-disable-next-line no-restricted-syntax
  if (!actor) {
    return <Card style={{ minHeight: '6vh', overflow: 'auto' }}>
      <CardContent>
        <Typography variant="h6">No player character</Typography>
      </CardContent>
    </Card>;
  }

  return <Card style={{ minHeight: '6vh', overflow: 'auto' }}>
    <CardContent>
      <Stack direction="column" spacing={2}>
        {activeTurn && <Alert severity="warning">It's your turn!</Alert>}
        <Typography variant="h6">Playing as: {actor.name}</Typography>
        <Typography variant="body1">{actor.backstory}</Typography>
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
