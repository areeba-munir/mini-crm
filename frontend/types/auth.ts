export type User = {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type RegisterInput = {
  full_name: string;
  email: string;
  password: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type UserUpdateInput = {
  full_name?: string;
  email?: string;
};

export type PasswordChangeInput = {
  current_password: string;
  new_password: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};
