import { Maybe, doesExist } from '@apextoaster/js-utils';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Typography } from '@mui/material';
import { instance as graphviz } from '@viz-js/viz';
import React, { Fragment, useEffect } from 'react';
import { useStore } from 'zustand';
import { Actor, Item, Room, World } from './models';
import { StoreState, store } from './store';

export interface EntityDetailsProps {
  entity: Maybe<Item | Actor | Room>;
  onClose: () => void;
  onRender: (type: string, entity: string) => void;
}

export function EntityDetails(props: EntityDetailsProps) {
  const { entity, onClose, onRender } = props;

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
      <Button onClick={() => onRender(entity.type, entity.name)}>Render</Button>
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

export function isWorld(entity: Maybe<Item | Actor | Room | World>): entity is World {
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
