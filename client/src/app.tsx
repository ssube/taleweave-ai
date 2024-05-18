/* eslint-disable @typescript-eslint/no-explicit-any */
import { Maybe, doesExist } from '@apextoaster/js-utils';
import {
  Container,
  CssBaseline,
  Stack,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import { Allotment } from 'allotment';
import React, { useEffect } from 'react';
import useWebSocketModule from 'react-use-websocket';
import { useStore } from 'zustand';

import { HistoryPanel } from './history.js';
import { Actor } from './models.js';
import { PlayerPanel } from './player.js';
import { Statusbar } from './status.js';
import { StoreState, store } from './store.js';
import { WorldPanel } from './world.js';

import 'allotment/dist/style.css';
import { DetailDialog } from './details.js';
import './main.css';

const useWebSocket = (useWebSocketModule as any).default;

export interface AppProps {
  socketUrl: string;
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

  // socket senders
  function renderEntity(type: string, entity: string) {
    sendMessage(JSON.stringify({ type: 'render', [type]: entity }));
  }

  function renderEvent(event: string) {
    sendMessage(JSON.stringify({ type: 'render', event }));
  }

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
          setClientId(event.client);
          return;
        case 'prompt':
          // prompts are broadcast to all players
          // only notify the active player
          setActiveTurn(event.client === clientId);
          break;
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
    <DetailDialog renderEntity={renderEntity} />
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
              <HistoryPanel renderEntity={renderEntity} renderEvent={renderEvent} />
            </Stack>
          </Allotment>
        </Stack>
      </Stack>
    </Container>
  </ThemeProvider>;
}
