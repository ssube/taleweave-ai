import { doesExist } from '@apextoaster/js-utils';
import { Alert, Card, CardContent, Stack, Typography } from '@mui/material';
import React from 'react';
import { useStore } from 'zustand';
import { store, StoreState } from './store';

export function playerStateSelector(s: StoreState) {
  return {
    character: s.playerCharacter,
    promptEvent: s.promptEvent,
  };
}

export function PlayerPanel() {
  const state = useStore(store, playerStateSelector);
  const { character, promptEvent } = state;

  if (doesExist(character)) {
    return <Card style={{ minHeight: '6vh', overflow: 'auto' }}>
      <CardContent>
        <Stack direction="column" spacing={2}>
          {doesExist(promptEvent) && <Alert severity="warning">It's your turn!</Alert>}
          <Typography variant="h6">Playing as: {character.name}</Typography>
          <Typography variant="body1">{character.backstory}</Typography>
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
