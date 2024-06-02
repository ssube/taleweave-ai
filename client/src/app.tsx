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
import { Character } from './models.js';
import { PlayerPanel } from './player.js';
import { Statusbar } from './status.js';
import { StoreState, store } from './store.js';
import { WorldPanel } from './world.js';
import { DetailDialog } from './details.js';
import { PromptDialog } from './prompt.js';

import 'allotment/dist/style.css';
import './main.css';

const useWebSocket = (useWebSocketModule as any).default;

export interface AppProps {
  socketUrl: string;
}

export function appStateSelector(s: StoreState) {
  return {
    layoutMode: s.layoutMode,
    themeMode: s.themeMode,
    setReadyState: s.setReadyState,
  };
}

export function App(props: AppProps) {
  const state = useStore(store, appStateSelector);
  const { layoutMode, themeMode, setReadyState } = state;

  // socket stuff
  const { lastMessage, readyState, sendMessage } = useWebSocket(props.socketUrl);

  function renderEntity(type: string, entity: string) {
    sendMessage(JSON.stringify({ type: 'render', [type]: entity }));
  }

  function renderEvent(event: string) {
    sendMessage(JSON.stringify({ type: 'render', event }));
  }

  function setPlayer(character: Maybe<Character>) {
    // do not call setCharacter until the server confirms the player change
    // eslint-disable-next-line no-null/no-null
    let become = null;
    if (doesExist(character)) {
      become = character.name;
    }
    sendMessage(JSON.stringify({ type: 'player', become }));
  }

  function sendInput(input: string) {
    const { playerCharacter: character, setPromptEvent } = store.getState();
    if (doesExist(character)) {
      sendMessage(JSON.stringify({ type: 'input', input }));
      setPromptEvent(undefined);
    }
  }

  function skipPrompt() {
    const { setPromptEvent } = store.getState();
    setPromptEvent(undefined);
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
    const { setClientId, setPromptEvent, setPlayers, appendEvent, setTurn, setWorld, world, clientId, setPlayerCharacter: setCharacter } = store.getState();
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
          if (event.client === clientId) {
            // only notify the active player
            setPromptEvent(event);
          } else {
            // if it has moved on to another player, clear the prompt
            setPromptEvent(undefined);
          }
          break;
        case 'player':
          if (doesExist(world) && event.client === clientId) {
            switch (event.status) {
              case 'join': {
                const { character: characterName } = event;
                const character = world.rooms.flatMap((room) => room.characters).find((a) => a.name === characterName);
                setCharacter(character);
                break;
              }
              case 'leave':
                setCharacter(undefined);
                break;
              default:
                // ignore other player events
            }
          }
          break;
        case 'players':
          setPlayers(event.players);
          return;
        case 'snapshot':
          setWorld(event.world);
          setTurn(event.turn);
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

  function innerLayout(a: React.JSX.Element, b: React.JSX.Element) {
    switch (layoutMode) {
      case 'horizontal':
        return <Allotment className='body-allotment'>{a}{b}</Allotment>;
      case 'vertical':
      default:
        return <Stack direction='column'>{a}{b}</Stack>;
    }
  }

  const layoutWidths = {
    // eslint-disable-next-line @typescript-eslint/no-magic-numbers
    horizontal: [400, 600],
    // eslint-disable-next-line @typescript-eslint/no-magic-numbers
    vertical: [1000, 1000],
  };
  const [leftWidth, rightWidth] = layoutWidths[layoutMode];

  return <ThemeProvider theme={theme}>
    <CssBaseline />
    <DetailDialog renderEntity={renderEntity} />
    <PromptDialog sendInput={sendInput} skipPrompt={skipPrompt} />
    <Container maxWidth='xl'>
      <Stack direction="column">
        <Statusbar setName={setName} />
        <Stack direction="row" spacing={2}>
          {innerLayout(
            <Stack direction="column" spacing={2} sx={{ minWidth: leftWidth }} className="scroll-history">
              <PlayerPanel />
              <WorldPanel setPlayer={setPlayer} />
            </Stack>,
            <Stack direction="column" sx={{ minWidth: rightWidth }} className="scroll-history">
              <HistoryPanel renderEntity={renderEntity} renderEvent={renderEvent} />
            </Stack>
          )}
        </Stack>
      </Stack>
    </Container>
  </ThemeProvider>;
}
