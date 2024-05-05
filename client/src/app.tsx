/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, Fragment } from 'react';
import useWebSocketModule, { ReadyState } from 'react-use-websocket';
import { Maybe, doesExist } from '@apextoaster/js-utils';
import {
  Button,
  CssBaseline,
  Dialog,
  DialogContent,
  DialogTitle,
  PaletteMode,
  ThemeProvider,
  createTheme,
  List,
  Divider,
  Typography,
  Container,
  Stack,
  Alert,
  Switch,
} from '@mui/material';
import { Allotment } from 'allotment';

import { Room, Actor, Item, World, WorldPanel, SetDetails } from './world.js';
import { EventItem } from './events.js';
import { PlayerPanel } from './player.js';

import 'allotment/dist/style.css';
import './main.css';

const useWebSocket = (useWebSocketModule as any).default;

const statusStrings = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Running',
  [ReadyState.CLOSING]: 'Closing',
  [ReadyState.CLOSED]: 'Closed',
  [ReadyState.UNINSTANTIATED]: 'Unready',
};

export function interleave(arr: Array<any>) {
  // eslint-disable-next-line @typescript-eslint/no-magic-numbers
  return arr.reduce((acc, val, idx) => acc.concat(val, <Divider component='li' key={`sep-${idx}`} variant='inset' />), []).slice(0, -1);
}

export interface AppProps {
  socketUrl: string;
}

export function EntityDetails(props: { entity: Maybe<Item | Actor | Room>; close: () => void }) {
  // eslint-disable-next-line no-restricted-syntax
  if (!doesExist(props.entity)) {
    return <Fragment />;
  }

  return <Fragment>
    <DialogTitle>{props.entity.name}</DialogTitle>
    <DialogContent>
      <Typography>
        {props.entity.description}
      </Typography>
      <Button onClick={() => props.close()}>Close</Button>
    </DialogContent>
  </Fragment>;
}

export function DetailDialog(props: { setDetails: SetDetails; details: Maybe<Item | Actor | Room> }) {
  const { details, setDetails } = props;

  return <Dialog
    open={doesExist(details)}
    onClose={() => setDetails(undefined)}
  >
    <EntityDetails entity={details} close={() => setDetails(undefined)} />
  </Dialog>;
}

export function App(props: AppProps) {
  const [ activeTurn, setActiveTurn ] = useState<boolean>(false);
  const [ detailEntity, setDetailEntity ] = useState<Maybe<Item | Actor | Room>>(undefined);
  const [ character, setCharacter ] = useState<Maybe<Actor>>(undefined);
  const [ clientId, setClientId ] = useState<string>('');
  const [ world, setWorld ] = useState<Maybe<World>>(undefined);
  const [ themeMode, setThemeMode ] = useState('light');
  const [ history, setHistory ] = useState<Array<string>>([]);
  const { lastMessage, readyState, sendMessage } = useWebSocket(props.socketUrl);

  function setPlayer(actor: Maybe<Actor>) {
    // do not setCharacter until the server confirms the player change
    if (doesExist(actor)) {
      sendMessage(JSON.stringify({ type: 'player', become: actor.name }));
    }
  }

  function sendInput(input: string) {
    if (doesExist(character)) {
      sendMessage(JSON.stringify({ type: 'input', input }));
      setActiveTurn(false);
    }
  }

  const theme = createTheme({
    palette: {
      mode: themeMode as PaletteMode,
    },
  });

  const connectionStatus = statusStrings[readyState as ReadyState];

  useEffect(() => {
    if (doesExist(lastMessage)) {
      const data = JSON.parse(lastMessage.data);

      if (data.type === 'id') {
        setClientId(data.id);
        return;
      }

      if (data.type === 'prompt') {
        if (data.id === clientId) {
          // notify the player and show the prompt
          setActiveTurn(true);
        } else {
          const message = `Waiting for ${data.character} to take their turn`;
          setHistory((prev) => prev.concat(message));
        }
        return;
      }

      setHistory((prev) => prev.concat(data));

      // if we get a world event, update the last world state
      if (data.type === 'world') {
        setWorld(data.world);
      }

      if (data.type === 'player' && data.id === clientId) {
        // find the actor that matches the player name
        const { name } = data;
        // eslint-disable-next-line no-restricted-syntax
        const actor = world?.rooms.flatMap((room) => room.actors).find((a) => a.name === name);
        setCharacter(actor);
      }
    }
  }, [lastMessage]);

  const items = history.map((item, index) => <EventItem key={`item-${index}`} event={item} />);

  return <ThemeProvider theme={theme}>
    <CssBaseline />
    <DetailDialog details={detailEntity} setDetails={setDetailEntity} />
    <Container maxWidth='xl'>
      <Stack direction="column">
        <Alert icon={false} severity="success">
          <Stack direction="row" alignItems="center" gap={4}>
            <Typography>
              Status: {connectionStatus}
            </Typography>
            <Switch
              checked={themeMode === 'dark'}
              onChange={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
              inputProps={{ 'aria-label': 'controlled' }}
              sx={{ marginLeft: 'auto' }}
            />
          </Stack>
        </Alert>
        <Stack direction="row" spacing={2}>
          <Allotment className='body-allotment'>
            <Stack direction="column" spacing={2} sx={{ minWidth: 400 }} className="scroll-history">
              <WorldPanel world={world} activeCharacter={character} setDetails={setDetailEntity} setPlayer={setPlayer} />
              <PlayerPanel actor={character} activeTurn={activeTurn} setDetails={setDetailEntity} sendInput={sendInput}  />
            </Stack>
            <Stack direction="column" sx={{ minWidth: 600 }}>
              <List sx={{ width: '100%', bgcolor: 'background.paper' }} className="scroll-history">
                {interleave(items)}
              </List>
            </Stack>
          </Allotment>
        </Stack>
      </Stack>
    </Container>
  </ThemeProvider>;
}
