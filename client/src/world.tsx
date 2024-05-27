import { Maybe, doesExist } from '@apextoaster/js-utils';
import { Card, CardContent, Divider, Stack, Typography } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import React from 'react';

import { useStore } from 'zustand';
import { StoreState, store } from './store';
import { Character, Item, Portal, Room } from './models';

export type SetDetails = (entity: Maybe<Item | Character | Room>) => void;
export type SetPlayer = (character: Maybe<Character>) => void;

export interface BaseEntityItemProps {
  setPlayer: SetPlayer;
}

export function formatLabel(name: string, active = false): string {
  if (active) {
    return `${name} (!)`;
  }

  return name;
}

export function itemStateSelector(s: StoreState) {
  return {
    playerCharacter: s.playerCharacter,
    setDetailEntity: s.setDetailEntity,
  };
}

export function characterStateSelector(s: StoreState) {
  return {
    playerCharacter: s.playerCharacter,
    players: s.players,
    setDetailEntity: s.setDetailEntity,
  };
}

export function worldStateSelector(s: StoreState) {
  return {
    turn: s.turn,
    world: s.world,
    setDetailEntity: s.setDetailEntity,
  };
}

export function PortalItem(props: { portal: Portal } & BaseEntityItemProps) {
  const { portal } = props;
  const state = useStore(store, itemStateSelector);
  const { setDetailEntity } = state;

  return <TreeItem itemId={`${portal.name}-portal`} label={portal.name}>
    <TreeItem itemId={`${portal.name}-details`} label="Details" onClick={() => setDetailEntity(portal)} />
  </TreeItem>;
}

export function ItemItem(props: { item: Item } & BaseEntityItemProps) {
  const { item } = props;
  const state = useStore(store, itemStateSelector);
  const { setDetailEntity } = state;

  return <TreeItem itemId={item.name} label={item.name}>
    <TreeItem itemId={`${item.name}-details`} label="Details" onClick={() => setDetailEntity(item)} />
  </TreeItem>;
}

export function CharacterItem(props: { character: Character } & BaseEntityItemProps) {
  const { character, setPlayer } = props;
  const state = useStore(store, characterStateSelector);
  const { playerCharacter, players, setDetailEntity } = state;

  const activeSelf = doesExist(playerCharacter) && character.name === playerCharacter.name;
  const activeOther = Object.values(players).some((it) => it === character.name); // TODO: are these the keys or the values?
  const label = formatLabel(character.name, activeSelf);

  let playButton;
  if (activeSelf) {
    playButton = <TreeItem itemId={`${character.name}-stop`} label="Stop playing" onClick={() => setPlayer(undefined)} />;
  } else {
    if (activeOther) {
      // eslint-disable-next-line no-restricted-syntax
      const player = Object.entries(players).find((it) => it[1] === character.name)?.[0];
      playButton = <TreeItem itemId={`${character.name}-taken`} label={`Played by ${player}`} />;
    } else {
      playButton = <TreeItem itemId={`${character.name}-play`} label="Play!" onClick={() => setPlayer(character)} />;
    }
  }

  return <TreeItem itemId={character.name} label={label}>
    {playButton}
    <TreeItem itemId={`${character.name}-details`} label="Details" onClick={() => setDetailEntity(character)} />
    <TreeItem itemId={`${character.name}-items`} label="Items">
      {character.items.map((item) => <ItemItem key={item.name} item={item} setPlayer={setPlayer} />)}
    </TreeItem>
  </TreeItem>;
}

export function RoomItem(props: { room: Room } & BaseEntityItemProps) {
  const { room, setPlayer } = props;
  const state = useStore(store, itemStateSelector);
  const { playerCharacter, setDetailEntity } = state;

  const active = doesExist(playerCharacter) && room.characters.some((it) => it.name === playerCharacter.name);
  const label = formatLabel(room.name, active);

  return <TreeItem itemId={room.name} label={label}>
    <TreeItem itemId={`${room.name}-details`} label="Details" onClick={() => setDetailEntity(room)} />
    <TreeItem itemId={`${room.name}-characters`} label="Characters">
      {room.characters.map((character) => <CharacterItem key={character.name} character={character} setPlayer={setPlayer} />)}
    </TreeItem>
    <TreeItem itemId={`${room.name}-items`} label="Items">
      {room.items.map((item) => <ItemItem key={item.name} item={item} setPlayer={setPlayer} />)}
    </TreeItem>
    <TreeItem itemId={`${room.name}-portals`} label="Portals">
      {room.portals.map((portal) => <PortalItem key={portal.name} portal={portal} setPlayer={setPlayer} />)}
    </TreeItem>
  </TreeItem>;
}

export function WorldPanel(props: BaseEntityItemProps) {
  const { setPlayer } = props;
  const state = useStore(store, worldStateSelector);
  const { turn, world, setDetailEntity } = state;

  // eslint-disable-next-line no-restricted-syntax
  if (!doesExist(world)) {
    return <Card style={{ minHeight: '6vh', overflow: 'auto' }}>
      <CardContent>
        <Typography variant="h6">
          No world data available
        </Typography>
      </CardContent>
    </Card>;
  }

  return <Card style={{ minHeight: 200, overflow: 'auto' }}>
    <CardContent>
      <Stack direction="column" spacing={2}>
        <Typography gutterBottom variant="h5" component="div">{world.name}</Typography>
        <Typography variant="body1">
          Theme: {world.theme}
        </Typography>
        <Typography variant="body2">
          Turn: {turn}
        </Typography>
        <Divider />
        <SimpleTreeView>
          <TreeItem itemId="world-graph" label="Graph" onClick={() => setDetailEntity(world)} />
          {world.rooms.map((room) => <RoomItem key={room.name} room={room} setPlayer={setPlayer} />)}
        </SimpleTreeView>
      </Stack>
    </CardContent>
  </Card>;
}
