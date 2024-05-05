import { ListItem, ListItemText, ListItemAvatar, Avatar, Typography } from '@mui/material';
import React from 'react';

import { formatters } from './format.js';

export interface EventItemProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  event: any;
}

export function ActionItem(props: EventItemProps) {
  const { event } = props;
  const { actor, room, type } = event;
  const content = formatters[type](event);

  return <ListItem alignItems="flex-start">
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

  return <ListItem alignItems="flex-start">
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

  return <ListItem alignItems="flex-start">
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
  const { name } = event;

  return <ListItem alignItems="flex-start">
    <ListItemAvatar>
      <Avatar alt={name} src="/static/images/avatar/1.jpg" />
    </ListItemAvatar>
    <ListItemText
      primary="New Player"
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >
          Someone is playing as {name}
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
      return <ActionItem event={event} />;
    case 'event':
      return <MessageItem event={event} />;
    case 'player':
      return <PlayerItem event={event} />;
    case 'world':
      return <WorldItem event={event} />;
    default:
      return <ListItem>
        <ListItemText primary={`Unknown event type: ${type}`} />
      </ListItem>;
  }
}
