import { Avatar, IconButton, ImageList, ImageListItem, ListItem, ListItemAvatar, ListItemText, Typography } from '@mui/material';
import React, { Fragment, MutableRefObject } from 'react';

import { Camera } from '@mui/icons-material';
import { formatters } from './format.js';
import { GameEvent } from './models.js';

export function openImage(image: string) {
  const byteCharacters = atob(image);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  const file = new Blob([byteArray], { type: 'image/jpeg;base64' });
  const fileURL = URL.createObjectURL(file);
  window.open(fileURL, '_blank');
}

export interface EventItemProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  event: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  focusRef?: MutableRefObject<any>;

  renderEvent: (event: GameEvent) => void;
}

export function ActionEventItem(props: EventItemProps) {
  const { event, renderEvent } = props;
  const { id, actor, room, type } = event;
  const content = formatters[type](event);

  return <ListItem
    alignItems="flex-start"
    ref={props.focusRef}
    secondaryAction={
      <IconButton edge="end" aria-label="render" onClick={() => renderEvent(id)}>
        <Camera />
      </IconButton>
    }
  >
    <ListItemAvatar>
      <Avatar alt={actor.name} src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary={room.name}
      secondary={
        <React.Fragment>
          <Typography
            sx={{ display: 'block' }}
            component="span"
            variant="body2"
            color="text.primary"
          >
            {actor.name}
          </Typography>
          {content}
        </React.Fragment>
      }
    />
  </ListItem>;
}

export function SnapshotEventItem(props: EventItemProps) {
  const { event } = props;
  const { step, world } = event;
  const { name, theme } = world;

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
    <ListItemAvatar>
      <Avatar alt={step.toString()} src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary={name}
      secondary={
        <Fragment>
          <Typography
            sx={{ display: 'block' }}
            component="span"
            variant="body2"
            color="text.primary"
          >
            Step: {step}
          </Typography>
          World Theme: {theme}
        </Fragment>
      }
    />
  </ListItem>;
}

export function ReplyEventItem(props: EventItemProps) {
  const { event } = props;
  const { text } = event;

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
    <ListItemAvatar>
      <Avatar alt="System" src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary="System"
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >
          {text}
        </Typography>
      }
    />
  </ListItem>;
}

export function PlayerEventItem(props: EventItemProps) {
  const { event } = props;
  const { character, status, client } = event;

  let primary = '';
  let secondary = '';
  if (status === 'join') {
    primary = 'Player Joined';
    secondary = `${client} is now playing as ${character}`;
  }
  if (status === 'leave') {
    primary = 'Player Left';
    secondary = `${client} has left the game. ${character} is now controlled by an LLM`;
  }

  return <ListItem
    alignItems="flex-start"
    ref={props.focusRef}
  >
    <ListItemAvatar>
      <Avatar alt={character} src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary={primary}
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >
          {secondary}
        </Typography>
      }
    />
  </ListItem>;
}

export function RenderEventItem(props: EventItemProps) {
  const { event } = props;
  const { images } = event;

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
    <ListItemAvatar>
      <Avatar alt="Render" src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary="Render"
      secondary={<ImageList cols={3} rowHeight={256}>
        {Object.entries(images).map(([name, image]) => <ImageListItem key={name}>
          <img src={`data:image/jpeg;base64,${image}`} onClick={() => openImage(image)} alt="Render" />
        </ImageListItem>)}
      </ImageList>}
    />
  </ListItem>;
}

export function EventItem(props: EventItemProps) {
  const { event } = props;
  const { type } = event;

  switch (type) {
    case 'action':
    case 'result':
      return <ActionEventItem {...props} />;
    case 'reply':
    case 'status': // TODO: should have a different component
      return <ReplyEventItem {...props} />;
    case 'player':
      return <PlayerEventItem {...props} />;
    case 'render':
      return <RenderEventItem {...props} />;
    case 'snapshot':
      return <SnapshotEventItem {...props} />;
    default:
      return <ListItem ref={props.focusRef}>
        <ListItemText primary={`Unknown event type: ${type}`} />
      </ListItem>;
  }
}
