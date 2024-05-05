import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import { Card, CardContent, CardHeader, Stack, Typography } from '@mui/material';
import { Maybe, doesExist } from '@apextoaster/js-utils';
import React from 'react';

export interface Item {
  name: string;
  description: string;
}

export interface Actor {
  name: string;
  backstory: string;
  description: string;
  items: Array<Item>;
}

export interface Room {
  name: string;
  description: string;
  portals: Record<string, string>;
  actors: Array<Actor>;
  items: Array<Item>;
}

export interface World {
  name: string;
  order: Array<string>;
  rooms: Array<Room>;
  theme: string;
}

export type SetDetails = (entity: Maybe<Item | Actor | Room>) => void;
export type SetPlayer = (actor: Maybe<Actor>) => void;

export interface BaseEntityItemProps {
  activeCharacter: Maybe<Actor>;
  setDetails: SetDetails;
  setPlayer: SetPlayer;
}

export function formatLabel(name: string, active = false): string {
  if (active) {
    return `${name} (!)`;
  }

  return name;
}

export function ItemItem(props: { item: Item } & BaseEntityItemProps) {
  const { item, setDetails } = props;

  return <TreeItem itemId={item.name} label={item.name}>
    <TreeItem itemId={`${item.name}-details`} label="Details" onClick={() => setDetails(item)} />
  </TreeItem>;
}

export function ActorItem(props: { actor: Actor } & BaseEntityItemProps) {
  const { actor, activeCharacter, setDetails, setPlayer } = props;

  const active = doesExist(activeCharacter) && actor.name === activeCharacter.name;
  const label = formatLabel(actor.name, active);

  let playButton;
  if (active === false) {
    playButton = <TreeItem itemId={`${actor.name}-play`} label="Play!" onClick={() => setPlayer(actor)} />;
  }

  return <TreeItem itemId={actor.name} label={label}>
    {playButton}
    <TreeItem itemId={`${actor.name}-details`} label="Details" onClick={() => setDetails(actor)} />
    <TreeItem itemId={`${actor.name}-items`} label="Items">
      {actor.items.map((item) => <ItemItem key={item.name} item={item} activeCharacter={activeCharacter} setDetails={setDetails} setPlayer={setPlayer} />)}
    </TreeItem>
  </TreeItem>;
}

export function RoomItem(props: { room: Room } & BaseEntityItemProps) {
  const { room, activeCharacter, setDetails, setPlayer } = props;

  const active = doesExist(activeCharacter) && room.actors.some((it) => it.name === activeCharacter.name);
  const label = formatLabel(room.name, active);

  return <TreeItem itemId={room.name} label={label}>
    <TreeItem itemId={`${room.name}-details`} label="Details" onClick={() => setDetails(room)} />
    <TreeItem itemId={`${room.name}-actors`} label="Actors">
      {room.actors.map((actor) => <ActorItem key={actor.name} actor={actor} activeCharacter={activeCharacter} setDetails={setDetails} setPlayer={setPlayer} />)}
    </TreeItem>
    <TreeItem itemId={`${room.name}-items`} label="Items">
      {room.items.map((item) => <ItemItem key={item.name} item={item} activeCharacter={activeCharacter} setDetails={setDetails} setPlayer={setPlayer} />)}
    </TreeItem>
  </TreeItem>;
}

export function WorldPanel(props: { world: Maybe<World> } & BaseEntityItemProps) {
  const { world, activeCharacter, setDetails, setPlayer } = props;

  // eslint-disable-next-line no-restricted-syntax
  if (!doesExist(world)) {
    return <Typography variant="h4">
      No world data available
    </Typography>;
  }

  return <Card>
    <CardContent>
      <Typography gutterBottom variant="h5" component="div">{world.name}</Typography>
      <Typography variant="body1">
        Theme: {world.theme}
      </Typography>
      <SimpleTreeView>
        {world.rooms.map((room) => <RoomItem key={room.name} room={room} activeCharacter={activeCharacter} setDetails={setDetails} setPlayer={setPlayer} />)}
      </SimpleTreeView>
    </CardContent>
  </Card>;
}
