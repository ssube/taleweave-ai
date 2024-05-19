import { Avatar, IconButton, ImageList, ImageListItem, ListItem, ListItemAvatar, ListItemText, Typography } from '@mui/material';
import React, { Fragment, MutableRefObject } from 'react';

import { Maybe, doesExist } from '@apextoaster/js-utils';
import { Camera, Settings } from '@mui/icons-material';
import { useStore } from 'zustand';
import { formatters } from './format.js';
import { Actor } from './models.js';
import { StoreState, store } from './store.js';

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

  renderEntity: (type: string, entity: string) => void;
  renderEvent: (event: string) => void;
}

export function characterSelector(state: StoreState) {
  return {
    character: state.character,
  };
}

export function sameCharacter(a: Maybe<Actor>, b: Maybe<Actor>): boolean {
  if (doesExist(a) && doesExist(b)) {
    return a.name === b.name;
  }

  return false;
}

export function ActionEventItem(props: EventItemProps) {
  const { event, renderEvent } = props;
  const { id, actor, room, type } = event;
  const content = formatters[type](event);

  const state = useStore(store, characterSelector);
  const { character } = state;

  const playerAction = sameCharacter(actor, character);
  const typographyProps = {
    color: playerAction ? 'success.text' : 'primary.text',
  };

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
      <Avatar>{room.name.substring(0, 1)}</Avatar>
    </ListItemAvatar>
    <ListItemText
      primary={room.name}
      primaryTypographyProps={typographyProps}
      secondaryTypographyProps={typographyProps}
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
      <Avatar>{step}</Avatar>
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
      <Avatar alt="System">
        <Settings />
      </Avatar>
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
      <Avatar>{character.substring(0, 1)}</Avatar>
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
  const { images, prompt, title = 'Render' } = event;

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
    <ListItemAvatar>
      <Avatar alt="Render">
        <Camera />
      </Avatar>
    </ListItemAvatar>
    <ListItemText
      primary={title}
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >{prompt}</Typography>
      }
    />
    <ImageList cols={3} rowHeight={256}>
      {Object.entries(images).map(([name, image]) => <ImageListItem key={name}>
        <a href='#' onClick={() => openImage(image as string)}>
          <img src={`data:image/jpeg;base64,${image}`} alt="Render" style={{ maxHeight: 256, maxWidth: 256 }} />
        </a>
      </ImageListItem>)}
    </ImageList>
  </ListItem>;
}

export function PromptEventItem(props: EventItemProps) {
  const { event } = props;
  const { character, prompt } = event;

  const state = useStore(store, characterSelector);
  const { character: playerCharacter } = state;

  const playerPrompt = sameCharacter(playerCharacter, character);
  const typographyProps = {
    color: playerPrompt ? 'success.text' : 'primary.text',
  };

  return <ListItem alignItems="flex-start" ref={props.focusRef}>
    <ListItemAvatar>
      <Avatar>{character.substring(0, 1)}</Avatar>
    </ListItemAvatar>
    <ListItemText
      primary="Prompt"
      primaryTypographyProps={typographyProps}
      secondaryTypographyProps={typographyProps}
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >
          Prompt for {character}: {prompt}
        </Typography>
      }
    />
  </ListItem>;
}

export function GenerateEventItem(props: EventItemProps) {
  const { event, renderEntity } = props;
  const { entity, name } = event;

  let renderButton;
  if (doesExist(entity)) {
    renderButton = <IconButton edge="end" aria-label="render" onClick={() => renderEntity(entity.type, entity.name)}>
      <Camera />
    </IconButton>;
  }

  return <ListItem
    alignItems="flex-start"
    ref={props.focusRef}
    secondaryAction={renderButton}
  >
    <ListItemAvatar>
      <Avatar>{name.substring(0, 1)}</Avatar>
    </ListItemAvatar>
    <ListItemText
      primary="Generate"
      secondary={
        <Typography
          sx={{ display: 'block' }}
          component="span"
          variant="body2"
          color="text.primary"
        >
          {name}
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
    case 'prompt':
      return <PromptEventItem {...props} />;
    case 'generate':
      return <GenerateEventItem {...props} />;
    default:
      return <ListItem ref={props.focusRef}>
        <ListItemText primary={`Unknown event type: ${type}`} />
      </ListItem>;
  }
}
