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
    return <Card>
      <CardContent>
        <Typography variant="h6">No player character</Typography>
      </CardContent>
    </Card>;
  }

  return <Card>
    <CardContent>
      <Stack direction="column" spacing={2}>
        {activeTurn && <Alert severity="warning">It's your turn!</Alert>}
        <Typography variant="h6">Playing as: {actor.name}</Typography>
        <Typography variant="body1">{actor.backstory}</Typography>
        <Stack direction="row" spacing={2}>
          <TextField label="Input" variant="outlined" fullWidth value={input} onChange={(event) => setInput(event.target.value)} />
          <Button variant="contained" onClick={() => {
            setInput('');
            sendInput(input);
          }}>Send</Button>
        </Stack>
      </Stack>
    </CardContent>
  </Card>;
}
