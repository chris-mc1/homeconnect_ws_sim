import type { Entity } from './types'

export enum EntityPropertyType {
  SWITCH = 'switch',
  BOOLEAN = 'boolean',
  TEXT = 'text',
  ACCESS = 'access',
  VALUE = 'value',
  INTEGER = 'integer',
}

export enum EntityProperty {
  AVAILABLE = 'available',
  UID = 'uid',
  NAME = 'name',
  ACCESS = 'access',
  VALUE = 'value',
  VALUE_RAW = 'value_raw',
  MIN = 'min',
  MAX = 'max',
  STEP_SIZE = 'stepSize',
  NOTIFY_ON_CHANGE = 'notifyOnChange',
  INIT_VALUE = 'initValue',
  PASSWORD_PROTECTED = 'passwordProtected',
  HANDLING = 'handling',
  LEVEL = 'level',
  DEFAULT = 'default',
  LIVE_UPDATE = 'liveUpdate',
  REF_UID = 'refUID',
  OPTIONS = 'options',
  EXECUTION = 'execution',
  FULL_OPTION_SET = 'fullOptionSet',
  VALIDATE = 'validate',
  REF_CID = 'refCID',
  REF_DID = 'refDID',
  PROTOCOL_TYPE = 'protocolType',
  CONTENT_TYPE = 'contentType',
}
export type pptMetadata = {
  type: EntityPropertyType
  key: keyof Entity
}

export interface PropertyMetadata {
  [key: EntityProperty | string]: pptMetadata
}

export const entity_ppt: PropertyMetadata = {
  [EntityProperty.UID]: {
    type: EntityPropertyType.TEXT,
    key: 'uid',
  },
  [EntityProperty.VALUE]: {
    type: EntityPropertyType.VALUE,
    key: 'value',
  },
  [EntityProperty.VALUE_RAW]: {
    type: EntityPropertyType.TEXT,
    key: 'value_raw',
  },
  [EntityProperty.PROTOCOL_TYPE]: {
    type: EntityPropertyType.TEXT,
    key: 'protocolType',
  },
  [EntityProperty.CONTENT_TYPE]: {
    type: EntityPropertyType.TEXT,
    key: 'contentType',
  },
  [EntityProperty.ACCESS]: {
    type: EntityPropertyType.ACCESS,
    key: 'access',
  },
  [EntityProperty.AVAILABLE]: {
    type: EntityPropertyType.SWITCH,
    key: 'available',
  },
  [EntityProperty.MIN]: {
    type: EntityPropertyType.INTEGER,
    key: 'min',
  },
  [EntityProperty.MAX]: {
    type: EntityPropertyType.INTEGER,
    key: 'max',
  },
  [EntityProperty.STEP_SIZE]: {
    type: EntityPropertyType.INTEGER,
    key: 'step',
  },
}
