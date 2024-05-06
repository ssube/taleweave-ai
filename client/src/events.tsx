import { ListItem, ListItemText, ListItemAvatar, Avatar, Typography } from '@mui/material';
import React, { MutableRefObject } from 'react';

import { formatters } from './format.js';

export interface EventItemProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  event: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  focusRef?: MutableRefObject<any>;
}

export function ActionItem(props: EventItemProps) {
  const { event } = props;
  const { actor, room, type } = event;
  const content = formatters[type](event);

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
    <ListItemAvatar>
      <Avatar alt={actor} src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary={room}
      secondary={
        <React.Fragment>
          <Typography
            sx={{ display: 'block' }}
            component="span"
            variant="body2"
            color="text.primary"
          >
            {actor}
          </Typography>
          {content}
        </React.Fragment>
      }
    />
  </ListItem>;
}

export function WorldItem(props: EventItemProps) {
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

export function MessageItem(props: EventItemProps) {
  const { event } = props;
  const { message } = event;

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
          {message}
        </Typography>
      }
    />
  </ListItem>;
}

export function PlayerItem(props: EventItemProps) {
  const { event } = props;
  const { character, event: innerEvent, id } = event;

  let primary = '';
  let secondary = '';
  if (innerEvent === 'join') {
    primary = 'New Player';
    secondary = `${id} is now playing as ${character}`;
  }
  if (innerEvent === 'leave') {
    primary = 'Player Left';
    secondary = `${id} has left the game. ${character} is now controlled by an LLM`;
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
      return <ActionItem event={event} focusRef={props.focusRef} />;
    case 'event':
      return <MessageItem event={event} focusRef={props.focusRef} />;
    case 'player':
      return <PlayerItem event={event} focusRef={props.focusRef} />;
    case 'world':
      return <WorldItem event={event} focusRef={props.focusRef} />;
    default:
      return <ListItem ref={props.focusRef}>
        <ListItemText primary={`Unknown event type: ${type}`} />
      </ListItem>;
  }
}
