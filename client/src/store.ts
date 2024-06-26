import { createContext } from 'react';
import { createStore, StateCreator } from 'zustand';

import { doesExist, Maybe } from '@apextoaster/js-utils';
import { PaletteMode } from '@mui/material';
import { ReadyState } from 'react-use-websocket';
import { Character, GameEvent, Item, Portal, PromptEvent, Room, World } from './models';

export type LayoutMode = 'horizontal' | 'vertical';

export interface ClientState {
  autoScroll: boolean;
  clientId: string;
  clientName: string;
  detailEntity: Maybe<Item | Character | Portal | Room | World>;
  eventHistory: Array<GameEvent>;
  layoutMode: LayoutMode;
  readyState: ReadyState;
  themeMode: PaletteMode;

  // setters
  setAutoScroll: (autoScroll: boolean) => void;
  setClientId: (clientId: string) => void;
  setClientName: (name: string) => void;
  setDetailEntity: (entity: Maybe<Item | Character | Portal | Room | World>) => void;
  setLayoutMode: (mode: LayoutMode) => void;
  setReadyState: (state: ReadyState) => void;
  setThemeMode: (mode: PaletteMode) => void;

  // misc helpers
  appendEvent: (event: GameEvent) => void;
  clearDetailEntity: () => void;
  clearEventHistory: () => void;
}

export interface WorldState {
  players: Record<string, string>;
  turn: Maybe<number>;
  world: Maybe<World>;

  // setters
  setPlayers: (players: Record<string, string>) => void;
  setTurn: (turn: Maybe<number>) => void;
  setWorld: (world: Maybe<World>) => void;
}

export interface PlayerState {
  playerCharacter: Maybe<Character>;
  promptEvent: Maybe<PromptEvent>;

  // setters
  setPlayerCharacter: (character: Maybe<Character>) => void;
  setPromptEvent: (promptEvent: Maybe<PromptEvent>) => void;

  // misc helpers
  isActive: () => boolean;
  isPlaying: () => boolean;
}

export type StoreState = ClientState & WorldState & PlayerState;

export function createClientStore(): StateCreator<ClientState> {
  return (set) => ({
    autoScroll: true,
    clientId: '',
    clientName: '',
    detailEntity: undefined,
    eventHistory: [],
    layoutMode: 'horizontal',
    readyState: ReadyState.UNINSTANTIATED,
    themeMode: 'light',
    setAutoScroll(autoScroll) {
      set({ autoScroll });
    },
    setClientId(clientId) {
      set({ clientId });
    },
    setClientName(clientName) {
      set({ clientName });
    },
    setDetailEntity(detailEntity) {
      set({ detailEntity });
    },
    setLayoutMode(mode) {
      set({ layoutMode: mode });
    },
    setReadyState(state) {
      set({ readyState: state });
    },
    setThemeMode(themeMode) {
      set({ themeMode });
    },
    appendEvent(event) {
      set((state) => {
        const history = state.eventHistory.concat(event);
        return { eventHistory: history };
      });
    },
    clearDetailEntity() {
      set({ detailEntity: undefined });
    },
    clearEventHistory() {
      set({ eventHistory: [] });
    },
  });
}

export function createWorldStore(): StateCreator<WorldState> {
  return (set) => ({
    players: {},
    turn: undefined,
    world: undefined,
    setPlayers: (players) => set({ players }),
    setTurn: (turn) => set({ turn }),
    setWorld: (world) => set({ world }),
  });
}

export function createPlayerStore(): StateCreator<PlayerState> {
  return (set) => ({
    playerCharacter: undefined,
    promptEvent: undefined,
    setPlayerCharacter: (character: Maybe<Character>) => set({ playerCharacter: character }),
    setPromptEvent(promptEvent) {
      set({ promptEvent });
    },
    isActive() {
      return doesExist(this.playerCharacter) && doesExist(this.promptEvent);
    },
    isPlaying() {
      return doesExist(this.playerCharacter);
    },
  });
}

export function createStateStore() {
  return createStore<StoreState>((...args) => ({
    ...createClientStore()(...args),
    ...createWorldStore()(...args),
    ...createPlayerStore()(...args),
  }));
}

// TODO: make this not global
export const store = createStateStore();
export const storeContext = createContext(store);
