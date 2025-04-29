export interface Appliance {
  info: ApplianceInfo
  entities: Entity[]
}
export interface ApplianceInfo {
  haId: string
  type: string
  serialNumber: string
  brand: string
  mac: string
  featureMappingFileName: string
  deviceDescriptionFileName: string
  created: string
  connectionType: string
  key: string
}
export interface ApplianceDescription {
  info: DeviceInfo
  status: EntityDescription[]
  setting: EntityDescription[]
  event: EntityDescription[]
  command: EntityDescription[]
  option: EntityDescription[]
  program: EntityDescription[]
  activeProgram: EntityDescription
  selectedProgram: EntityDescription
  protectionPort: EntityDescription
}
export interface DeviceInfo {
  brand: string
  type: string
  model: string
  version: number
  revision: number
  deviceID: string
  eNumber: string
  vib: string
  mac: string
  haVersion: string
  swVersion: string
  hwVersion: string
  deviceType: string
  deviceInfo: string
  customerIndex: string
  serialNumber: string
  fdString: string
  shipSki: string
}
export interface EntityDescription {
  uid: number
  name: string
  enumeration: object
  available: boolean
  access: 'none' | 'read' | 'readwrite' | 'writeonly' | 'readstatic'
  min: number
  max: number
  stepSize: number
  notifyOnChange: boolean
  initValue: any
  passwordProtected: boolean
  handling: 'none' | 'acknowledge' | 'decision'
  level: 'info' | 'hint' | 'warning' | 'alert' | 'critical'
  default: any
  liveUpdate: boolean
  refUID: number
  options: OptionDescription[]
  execution: 'none' | 'selectonly' | 'startonly' | 'selectandstart'
  fullOptionSet: boolean
  validate: boolean
  refCID: number
  refDID: number
  protocolType: string
  contentType: string
}
export interface OptionDescription {
  access: 'none' | 'read' | 'readwrite' | 'writeonly' | 'readstatic'
  available: boolean
  liveUpdate: boolean
  refUID: number
  default: any
}
export enum EntityProtocolType {
  BOOLEAN = 'Boolean',
  INTEGER = 'Integer',
  FLOAT = 'Float',
  STRING = 'String',
  OBJECT = 'Object',
}

export interface Entity {
  uid: number
  name: string
  value: any
  value_raw: any
  enum: { [key: number]: string }
  access: 'none' | 'read' | 'readwrite' | 'writeonly' | 'readstatic' | null
  available: boolean | null
  min: number
  max: number
  step: number
  protocolType: EntityProtocolType
  contentType: string
}

// WS Message
export interface WsMessage {
  action: 'init' | 'update'
  entities: Entity[]
  entity: Entity
}

export type UpdateMessage = {
  [key in keyof Entity]: any | null
} & {
  uid: number
}
