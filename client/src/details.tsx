import { Maybe, doesExist } from '@apextoaster/js-utils';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { instance as graphviz } from '@viz-js/viz';
import React, { Fragment, useEffect } from 'react';
import { useStore } from 'zustand';
import { Character, Attributes, Item, Portal, Room, World } from './models';
import { StoreState, store } from './store';

export interface EntityDetailsProps {
  entity: Maybe<Item | Character | Portal | Room>;
  onClose: () => void;
  onRender: (type: string, entity: string) => void;
}

export function EntityDetails(props: EntityDetailsProps) {
  const { entity, onClose, onRender } = props;

  // eslint-disable-next-line no-restricted-syntax
  if (!doesExist(entity)) {
    return <Fragment />;
  }

  const { description, name, type } = entity;

  let attributes: Attributes = {};
  let planner;

  if (type === 'character') {
    const character = entity as Character;
    attributes = character.attributes;
    planner = character.planner;
  }

  if (type === 'item') {
    const item = entity as Item;
    attributes = item.attributes;
  }

  if (type === 'room') {
    const room = entity as Room;
    attributes = room.attributes;
  }

  return <Fragment>
    <DialogTitle>{name}</DialogTitle>
    <DialogContent dividers>
      <Stack direction='column' spacing={2}>
        <Typography>
          {description}
        </Typography>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Attribute</TableCell>
                <TableCell>Value</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(attributes).map(([key, value]) => (
                <TableRow key={key}>
                  <TableCell>{key}</TableCell>
                  <TableCell>{value}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        {doesExist(planner) && <List>
          {planner.notes.map((note: string) => (
            <ListItem>
              <ListItemText primary={note} />
            </ListItem>
          ))}
        </List>}
      </Stack>
    </DialogContent>
    <DialogActions>
      <Button onClick={() => onRender(type, name)}>Render</Button>
      <Button onClick={onClose}>Close</Button>
    </DialogActions>
  </Fragment>;
}

export interface WorldDetailsProps {
  world: World;
}

export function WorldDetails(props: WorldDetailsProps) {
  const { world } = props;

  useEffect(() => {
    graphviz().then((viz) => {
      const dot = worldGraph(world);
      const svg = viz.renderSVGElement(dot);
      const graph = document.getElementById('graph');
      if (doesExist(graph)) {
        graph.replaceChildren(svg);
      }
    }).catch((err) => {
      // eslint-disable-next-line no-console
      console.error(err);
    });
  }, [world]);

  return <Fragment>
    <DialogTitle>{world.name}</DialogTitle>
    <DialogContent dividers>
      <Typography variant='body2'>
        Theme: {world.theme}
      </Typography>
      <div id="graph" />
    </DialogContent>
  </Fragment>;
}

export function detailStateSelector(s: StoreState) {
  return {
    detailEntity: s.detailEntity,
    clearDetailEntity: s.clearDetailEntity,
  };
}

export interface DetailDialogProps {
  renderEntity: (type: string, entity: string) => void;
}

export function DetailDialog(props: DetailDialogProps) {
  const state = useStore(store, detailStateSelector);
  const { detailEntity, clearDetailEntity } = state;

  let details;
  if (isWorld(detailEntity)) {
    details = <WorldDetails world={detailEntity} />;
  } else {
    details = <EntityDetails entity={detailEntity} onClose={clearDetailEntity} onRender={props.renderEntity} />;
  }

  return <Dialog
    open={doesExist(detailEntity)}
    onClose={clearDetailEntity}
  >{details}</Dialog>;
}

export function isWorld(entity: Maybe<Item | Character | Portal | Room | World>): entity is World {
  return doesExist(entity) && doesExist(Object.getOwnPropertyDescriptor(entity, 'theme'));
}

export function worldGraph(world: World): string {
  return `digraph {
    ${world.rooms.map((room) => roomGraph(room).join('; ')).join('\n')}
  }`;
}

export function roomGraph(room: Room): Array<string> {
  return room.portals.map((portal) =>
    `"${room.name}" -> "${portal.destination}" [label="${portal.name}"]`
  );
}
