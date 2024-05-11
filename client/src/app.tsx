/* eslint-disable @typescript-eslint/no-explicit-any */
import { Maybe, doesExist } from '@apextoaster/js-utils';
import {
  Button,
  Container,
  CssBaseline,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  ThemeProvider,
  Typography,
  createTheme,
} from '@mui/material';
import { Allotment } from 'allotment';
import React, { Fragment, useEffect } from 'react';
import useWebSocketModule from 'react-use-websocket';
import { useStore } from 'zustand';

import { HistoryPanel } from './history.js';
import { Actor, Item, Room } from './models.js';
import { PlayerPanel } from './player.js';
import { store, StoreState } from './store.js';
import { WorldPanel } from './world.js';
import { Statusbar } from './status.js';

import 'allotment/dist/style.css';
import './main.css';

const useWebSocket = (useWebSocketModule as any).default;

export interface AppProps {
  socketUrl: string;
}

export interface EntityDetailsProps {
  entity: Maybe<Item | Actor | Room>;
  close: () => void;
}

export function EntityDetails(props: EntityDetailsProps) {
  const { entity, close } = props;

  // eslint-disable-next-line no-restricted-syntax
  if (!doesExist(entity)) {
    return <Fragment />;
  }

  return <Fragment>
    <DialogTitle>{entity.name}</DialogTitle>
    <DialogContent dividers>
      <Typography>
        {entity.description}
      </Typography>
    </DialogContent>
    <DialogActions>
      <Button onClick={close}>Close</Button>
    </DialogActions>
  </Fragment>;
}

export function detailStateSelector(s: StoreState) {
  return {
    detailEntity: s.detailEntity,
    clearDetailEntity: s.clearDetailEntity,
  };
}

export function DetailDialog() {
  const state = useStore(store, detailStateSelector);
  const { detailEntity, clearDetailEntity } = state;

  return <Dialog
    open={doesExist(detailEntity)}
    onClose={clearDetailEntity}
  >
    <EntityDetails entity={detailEntity} close={clearDetailEntity} />
  </Dialog>;
}

export function appStateSelector(s: StoreState) {
  return {
    themeMode: s.themeMode,
    setReadyState: s.setReadyState,
  };
}

export function App(props: AppProps) {
  const state = useStore(store, appStateSelector);
  const { themeMode, setReadyState } = state;

  // socket stuff
  const { lastMessage, readyState, sendMessage } = useWebSocket(props.socketUrl);

  function setPlayer(actor: Maybe<Actor>) {
    // do not call setCharacter until the server confirms the player change
    if (doesExist(actor)) {
      sendMessage(JSON.stringify({ type: 'player', become: actor.name }));
    }
  }

  function sendInput(input: string) {
    const { character, setActiveTurn } = store.getState();
    if (doesExist(character)) {
      sendMessage(JSON.stringify({ type: 'input', input }));
      setActiveTurn(false);
    }
  }

  function setName(name: string) {
    const { setClientName } = store.getState();
    sendMessage(JSON.stringify({ type: 'player', name }));
    setClientName(name);
  }

  const theme = createTheme({
    palette: {
      mode: themeMode,
    },
  });

  useEffect(() => {
    const { setClientId, setActiveTurn, setPlayers, appendEvent, setWorld, world, clientId, setCharacter } = store.getState();
    if (doesExist(lastMessage)) {
      const event = JSON.parse(lastMessage.data);

      // handle special events
      switch (event.type) {
        case 'id':
          // unicast the client id to the player, do not append to history
          setClientId(event.id);
          return;
        case 'prompt':
          // prompts are broadcast to all players
          if (event.client === clientId) {
            // only notify the active player
            setActiveTurn(true);
            break;
          } else {
            setActiveTurn(false);
            return;
          }
        case 'player':
          if (event.status === 'join' && doesExist(world) && event.client === clientId) {
            const { character: characterName } = event;
            const actor = world.rooms.flatMap((room) => room.actors).find((a) => a.name === characterName);
            setCharacter(actor);
          }
          break;
        case 'players':
          setPlayers(event.players);
          return;
        case 'snapshot':
          setWorld(event.world);
          break;
        default:
          // this is not concerning, other events are kept in history and displayed
      }

      appendEvent(event);
    }
  }, [lastMessage]);

  useEffect(() => {
    setReadyState(readyState);
  }, [readyState]);

  return <ThemeProvider theme={theme}>
    <CssBaseline />
    <DetailDialog />
    <Container maxWidth='xl'>
      <Stack direction="column">
        <Statusbar setName={setName} />
        <Stack direction="row" spacing={2}>
          <Allotment className='body-allotment'>
            <Stack direction="column" spacing={2} sx={{ minWidth: 400 }} className="scroll-history">
              <PlayerPanel sendInput={sendInput} />
              <WorldPanel setPlayer={setPlayer} />
            </Stack>
            <Stack direction="column" sx={{ minWidth: 600 }} className="scroll-history">
              <HistoryPanel />
            </Stack>
          </Allotment>
        </Stack>
      </Stack>
    </Container>
  </ThemeProvider>;
}
