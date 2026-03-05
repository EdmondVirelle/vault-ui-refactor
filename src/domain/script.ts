export type ScriptOption = {
  key: string;
  flag: string;
  help?: string | null;
  is_bool: boolean;
  takes_value: boolean;
  required: boolean;
};

export type ScriptInfo = {
  id: string;
  file_name: string;
  category: string;
  summary: string;
  options: ScriptOption[];
};
