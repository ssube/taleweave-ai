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
  FormGroup,
  FormControlLabel,
} from '@mui/material';
import { Allotment } from 'allotment';

import { Room, Actor, Item, World, WorldPanel, SetDetails } from './world.js';
import { EventItem } from './events.js';
import { PlayerPanel } from './player.js';

import 'allotment/dist/style.css';
import './main.css';
import { HistoryPanel } from './history.js';

const useWebSocket = (useWebSocketModule as any).default;

const statusStrings = {
  [ReadyState.CONNECTING]: 'Connecting',
  [ReadyState.OPEN]: 'Running',
  [ReadyState.CLOSING]: 'Closing',
  [ReadyState.CLOSED]: 'Closed',
  [ReadyState.UNINSTANTIATED]: 'Unready',
};

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
  const [ autoScroll, setAutoScroll ] = useState<boolean>(true);
  const [ detailEntity, setDetailEntity ] = useState<Maybe<Item | Actor | Room>>(undefined);
  const [ character, setCharacter ] = useState<Maybe<Actor>>(undefined);
  const [ clientId, setClientId ] = useState<string>('');
  const [ world, setWorld ] = useState<Maybe<World>>(undefined);
  const [ themeMode, setThemeMode ] = useState('light');
  const [ history, setHistory ] = useState<Array<string>>([]);
  const [ players, setPlayers ] = useState<Record<string, string>>({});
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
        // unicast the client id to the player
        setClientId(data.id);
        return;
      }

      if (data.type === 'prompt') {
        // prompts are broadcast to all players
        if (data.id === clientId) {
          // only notify the active player
          setActiveTurn(true);
        } else {
          const message = `Waiting for ${data.character} to take their turn`;
          setHistory((prev) => prev.concat(message));
        }
        return;
      }

      if (data.type === 'players') {
        setPlayers(data.players);
        return;
      }

      setHistory((prev) => prev.concat(data));

      // if we get a world event, update the last world state
      if (data.type === 'world') {
        setWorld(data.world);
      }

      if (doesExist(world) && data.type === 'player' && data.id === clientId && data.event === 'join') {
        // find the actor that matches the player name
        const { character: characterName } = data;
        const actor = world.rooms.flatMap((room) => room.actors).find((a) => a.name === characterName);
        setCharacter(actor);
      }
    }
  }, [lastMessage]);


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
            </FormGroup>
          </Stack>
        </Alert>
        <Stack direction="row" spacing={2}>
          <Allotment className='body-allotment'>
            <Stack direction="column" spacing={2} sx={{ minWidth: 400 }} className="scroll-history">
              <PlayerPanel actor={character} activeTurn={activeTurn} setDetails={setDetailEntity} sendInput={sendInput}  />
              <WorldPanel world={world} activeCharacter={character} setDetails={setDetailEntity} setPlayer={setPlayer} />
            </Stack>
            <Stack direction="column" sx={{ minWidth: 600 }} className="scroll-history">
              <HistoryPanel history={history} scroll={autoScroll ? 'instant' : false} />
            </Stack>
          </Allotment>
        </Stack>
      </Stack>
    </Container>
  </ThemeProvider>;
}
