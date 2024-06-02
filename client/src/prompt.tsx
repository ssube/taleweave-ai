import { Maybe, doesExist, mustDefault, mustExist } from '@apextoaster/js-utils';
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Divider, FormControlLabel, MenuItem, Stack, Switch, TextField } from '@mui/material';
import React from 'react';
import { useStore } from 'zustand';
import { World, BooleanParameter, NumberParameter, StringParameter, Parameter, Action } from './models';
import { StoreState, store } from './store';

// region parameter components
export interface BooleanParameterProps {
  name: string;
  parameter: BooleanParameter;

  setParameter: (value: boolean) => void;
}

export function BooleanParameterItem(props: BooleanParameterProps) {
  const { name, setParameter } = props;

  return <FormControlLabel control={<Switch onChange={(event) => setParameter(event.target.checked)} />} label={name} />;
}

export function EnumParameterItem(props: NumberParameterProps | StringParameterProps) {
  const { name, parameter, setParameter } = props;
  const enumValues = mustExist(parameter.enum);
  const defaultValue = mustDefault(parameter.default, enumValues[0]);

  return <TextField
    select
    label={name}
    variant="outlined"
    defaultValue={defaultValue}
    onChange={(event) => setParameter(event.target.value)}
  >
    {enumValues.map((value) => <MenuItem value={value}>{value}</MenuItem>)}
  </TextField>;
}

export interface NumberParameterProps {
  name: string;
  parameter: NumberParameter;

  setParameter: (value: number) => void;
}

export function NumberParameterItem(props: NumberParameterProps) {
  const { name, parameter, setParameter } = props;

  if (doesExist(parameter.enum)) {
    return <EnumParameterItem name={name} parameter={parameter} setParameter={setParameter} />;
  }

  return <TextField
    label={name}
    variant="outlined"
    defaultValue={parameter.default}
    onChange={(event) => setParameter(parseFloat(event.target.value))}
  />;
}

export interface StringParameterProps {
  name: string;
  parameter: StringParameter;

  setParameter: (value: string) => void;
}

export function StringParameterItem(props: StringParameterProps) {
  const { name, parameter, setParameter } = props;

  if (doesExist(parameter.enum)) {
    return <EnumParameterItem name={name} parameter={parameter} setParameter={setParameter} />;
  }

  return <TextField
    label={name}
    variant="outlined"
    defaultValue={parameter.default}
    onChange={(event) => setParameter(event.target.value)}
  />;
}

export interface UnknownParameterProps {
  name: string;
}

export function UnknownParameter(props: UnknownParameterProps) {
  const { name } = props;

  return <Alert severity="warning">Unknown parameter type: {name}</Alert>;
}
// endregion

export const SIGNIFICANT_PARAMETERS = ['character', 'direction', 'item', 'room', 'target'];

export function listCharacters(world: World) {
  return world.rooms.flatMap((room) => room.characters);
}

export function listItems(world: World) {
  return world.rooms.flatMap((room) => room.items);
}

export function listPortals(world: World) {
  return world.rooms.flatMap((room) => room.portals);
}

export function enumerateSignificantParameterValues(name: string, world: World) {
  switch (name) {
    case 'character':
      return listCharacters(world).map((character) => character.name);
    case 'direction':
      return listPortals(world).map((portal) => portal.name);
    case 'item':
      return listItems(world).map((item) => item.name);
    case 'room':
      return world.rooms.map((room) => room.name);
    case 'target':
    {
      const characters = listCharacters(world);
      const items = listItems(world);

      return [
        ...characters.map((character) => character.name),
        ...items.map((item) => item.name),
      ];
    }
    default:
      return [];
  }
}

export function convertSignificantParameter(name: string, parameter: Parameter, world: Maybe<World>): Parameter {
  if (parameter.type === 'boolean') {
    return parameter;
  }

  if (doesExist(world) && SIGNIFICANT_PARAMETERS.includes(name)) {
    return {
      ...parameter,
      enum: enumerateSignificantParameterValues(name, world),
    };
  }

  return parameter;
}

export function selectWorld(state: StoreState) {
  return {
    world: state.world,
  };
}

export function formatAction(action: string, parameters: Record<string, boolean | number | string>) {
  return `~${action}:${Object.entries(parameters).map(([name, value]) => `${name}=${value}`).join(',')}`;
}

export function makeDefaultParameterValues(parameters: Record<string, Parameter>) {
  return Object.entries(parameters).reduce((acc, [name, parameter]) => {
    switch (parameter.type) {
      case 'boolean':
        return { ...acc, [name]: mustDefault(parameter.default, false) };
      case 'number':
        return { ...acc, [name]: mustDefault(parameter.default, 0) };
      case 'string':
        return { ...acc, [name]: mustDefault(parameter.default, '') };
      default:
        return acc;
    }
  }, {} as Record<string, boolean | number | string>);
}

export interface PromptActionProps {
  action: Action;

  setAction: (action: string) => void;
}

export function PromptAction(props: PromptActionProps) {
  const { action, setAction } = props;
  const { world } = useStore(store, selectWorld);

  // initialize with default values
  const [parameterValues, setParameterValues] = React.useState(makeDefaultParameterValues(action.function.parameters.properties));

  // create an input for each parameter
  const inputs = Object.entries(action.function.parameters.properties).filter(([name, _parameter]) => name !== 'unused').map(([name, parameter]) => {
    const convertedParameter = convertSignificantParameter(name, parameter, world);

    switch (convertedParameter.type) {
      case 'string':
        return <StringParameterItem name={name} parameter={convertedParameter as StringParameter} setParameter={(value) => {
          setParameterValues((old) => ({ ...old, [name]: value }));
        }} />;
      case 'number':
        return <NumberParameterItem name={name} parameter={convertedParameter as NumberParameter} setParameter={(value) => {
          setParameterValues((old) => ({ ...old, [name]: value }));
        }} />;
      case 'boolean':
        return <BooleanParameterItem name={name} parameter={convertedParameter as BooleanParameter} setParameter={(value) => {
          setParameterValues((old) => ({ ...old, [name]: value }));
        }} />;
      default:
        return <UnknownParameter name={name} />;
    }
  });

  return <Stack direction='column' spacing={2}>
    <Button onClick={() => setAction(formatAction(action.function.name, parameterValues))}>{action.function.description}</Button>
    <Stack direction='row' spacing={2}>
      {inputs}
    </Stack>
  </Stack>;
}

export function selectPromptEvent(state: StoreState) {
  return {
    promptEvent: state.promptEvent,
  };
}

export interface PromptDialogProps {
  sendInput: (input: string) => void;
  skipPrompt: () => void;
}

export function PromptDialog(props: PromptDialogProps) {
  const { sendInput, skipPrompt } = props;
  const { promptEvent } = useStore(store, selectPromptEvent);

  const [input, setInput] = React.useState<string>('');

  // eslint-disable-next-line no-restricted-syntax
  if (!doesExist(promptEvent)) {
    return <Dialog open={false} />;
  }

  return <Dialog open={true}>
    <DialogTitle>It's your turn, {promptEvent.character.name}!</DialogTitle>
    <DialogContent>
      <Stack direction="column" spacing={2}>
        <DialogContentText>{promptEvent.prompt}</DialogContentText>
        <Divider />
        <DialogContentText>Select parameters first, then click the label to act.</DialogContentText>
        {promptEvent.actions.map((action: Action) => <PromptAction action={action} setAction={setInput} />)}
        <Divider />
        <Stack direction="row" spacing={2}>
          <TextField
            fullWidth
            label="Input"
            variant="outlined"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                sendInput(input);
                setInput('');
              }
            }}
          />
          <Button variant="contained" onClick={() => {
            sendInput(input);
            setInput('');
          }}>Enqueue</Button>
        </Stack>
      </Stack>
    </DialogContent>
    <DialogActions>
      <Button onClick={skipPrompt}>Skip</Button>
      <Button onClick={skipPrompt}>Leave</Button>
    </DialogActions>
  </Dialog>;
}
