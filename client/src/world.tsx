import { Maybe, doesExist } from '@apextoaster/js-utils';
import { Card, CardContent, Typography } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import React from 'react';

import { useStore } from 'zustand';
import { StoreState, store } from './store';
import { Actor, Item, Room } from './models';

export type SetDetails = (entity: Maybe<Item | Actor | Room>) => void;
export type SetPlayer = (actor: Maybe<Actor>) => void;

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
    character: s.character,
    setDetailEntity: s.setDetailEntity,
  };
}

export function worldStateSelector(s: StoreState) {
  return {
    world: s.world,
    setDetailEntity: s.setDetailEntity,
  };
}

export function ItemItem(props: { item: Item } & BaseEntityItemProps) {
  const { item } = props;
  const state = useStore(store, itemStateSelector);
  const { setDetailEntity } = state;

  return <TreeItem itemId={item.name} label={item.name}>
    <TreeItem itemId={`${item.name}-details`} label="Details" onClick={() => setDetailEntity(item)} />
  </TreeItem>;
}

export function ActorItem(props: { actor: Actor } & BaseEntityItemProps) {
  const { actor, setPlayer } = props;
  const state = useStore(store, itemStateSelector);
  const { character, setDetailEntity } = state;

  // TODO: include other players
  const active = doesExist(character) && actor.name === character.name;
  const label = formatLabel(actor.name, active);

  let playButton;
  if (active === false) {
    playButton = <TreeItem itemId={`${actor.name}-play`} label="Play!" onClick={() => setPlayer(actor)} />;
  }

  return <TreeItem itemId={actor.name} label={label}>
    {playButton}
    <TreeItem itemId={`${actor.name}-details`} label="Details" onClick={() => setDetailEntity(actor)} />
    <TreeItem itemId={`${actor.name}-items`} label="Items">
      {actor.items.map((item) => <ItemItem key={item.name} item={item} setPlayer={setPlayer} />)}
    </TreeItem>
  </TreeItem>;
}

export function RoomItem(props: { room: Room } & BaseEntityItemProps) {
  const { room, setPlayer } = props;
  const state = useStore(store, itemStateSelector);
  const { character, setDetailEntity } = state;

  const active = doesExist(character) && room.actors.some((it) => it.name === character.name);
  const label = formatLabel(room.name, active);

  return <TreeItem itemId={room.name} label={label}>
    <TreeItem itemId={`${room.name}-details`} label="Details" onClick={() => setDetailEntity(room)} />
    <TreeItem itemId={`${room.name}-actors`} label="Actors">
      {room.actors.map((actor) => <ActorItem key={actor.name} actor={actor} setPlayer={setPlayer} />)}
    </TreeItem>
    <TreeItem itemId={`${room.name}-items`} label="Items">
      {room.items.map((item) => <ItemItem key={item.name} item={item} setPlayer={setPlayer} />)}
    </TreeItem>
  </TreeItem>;
}

export function WorldPanel(props: BaseEntityItemProps) {
  const { setPlayer } = props;
  const state = useStore(store, worldStateSelector);
  const { world, setDetailEntity } = state;

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
      <Typography gutterBottom variant="h5" component="div">{world.name}</Typography>
      <Typography variant="body1">
        Theme: {world.theme}
      </Typography>
      <SimpleTreeView>
        <TreeItem itemId="world-graph" label="Graph" onClick={() => setDetailEntity(world)} />
        {world.rooms.map((room) => <RoomItem key={room.name} room={room} setPlayer={setPlayer} />)}
      </SimpleTreeView>
    </CardContent>
  </Card>;
}
