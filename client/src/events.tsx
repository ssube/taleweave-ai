import { ListItem, ListItemText, ListItemAvatar, Avatar, Typography } from '@mui/material';
import React, { MutableRefObject } from 'react';

import { formatters } from './format.js';

export interface EventItemProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  event: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  focusRef?: MutableRefObject<any>;
}

export function ActionEventItem(props: EventItemProps) {
  const { event } = props;
  const { actor, room, type } = event;
  const content = formatters[type](event);

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
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
  const { theme } = world;

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
    <ListItemAvatar>
      <Avatar alt={step.toString()} src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary={theme}
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >
          Step {step}
        </Typography>
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

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
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

export function EventItem(props: EventItemProps) {
  const { event } = props;
  const { type } = event;

  switch (type) {
    case 'action':
    case 'result':
      return <ActionEventItem event={event} focusRef={props.focusRef} />;
    case 'reply':
      return <ReplyEventItem event={event} focusRef={props.focusRef} />;
    case 'player':
      return <PlayerEventItem event={event} focusRef={props.focusRef} />;
    case 'snapshot':
      return <SnapshotEventItem event={event} focusRef={props.focusRef} />;
    default:
      return <ListItem ref={props.focusRef}>
        <ListItemText primary={`Unknown event type: ${type}`} />
      </ListItem>;
  }
}
