declare namespace Api {
  /**
   * MCP 服务器配置
   */
  type McpServerConfig = {
    /** 服务器类型 */
    type: string;
    /** 启动命令 */
    command?: string | null;
    /** 命令参数 */
    args?: string[] | null;
    /** 环境变量 */
    env?: Record<string, string> | null;
    /** 服务器URL */
    url?: string | null;
    /** 请求头配置 */
    headers?: Record<string, string> | null;
  }

  /**
   * MCP 服务器数据
   */
  type McpServersData = {
    /** 
     * MCP 服务器配置映射
     * @key 服务器名称或ID
     * @value 服务器配置
     */
    mcpServers: Record<string, McpServerConfig>;
  }
  /**
   * 创建模型配置的参数。
   * @param {string} provider_id - 模型供应商的ID。
   * @param {string} api_key - API密钥。
   * @param {string} base_url - 基础URL。
   */
  type CreateModelCfgParams = {
    provider_id: string;
    api_key: string;
    base_url: string;
  };

  /**
   * 删除模型配置的参数。
   * @param {string} id - 要删除的模型配置的ID。
   */
  type DeleteModelCfgParams = {
    id: string;
  };

  /**
   * 列出模型配置的参数。
   * 目前没有特定的查询参数。
   */
  type ListModelCfgParams = {
    // 可能将来会添加参数
  };

  /**
   * 列出模型供应商的参数。
   * 目前没有特定的查询参数。
   */
  type ListProvidersParams = {

  }
  
  /**
   * 列出默认设置模型参数。
   * 目前没有特定的查询参数。
   */
  type GetDefaultCfgParams = {

  }

  /**
   * 获取可用模型配置的参数。
   * @param {string} id - 模型配置的ID。
   */
  type GetAvailableModelCfgParams = {
    id: string;
  };

  /**
   * 设置默认模型配置的参数。
   * @param {string} model_cfg_id - 模型配置的ID。
   * @param {string} llm_name - 默认LLM模型。
   * @param {string} embedding_name - 默认embedding模型。
   */
  type SetDefaultModelCfgParams = {
    model_cfg_id: string;
    llm_name: string;
    embedding_name: string;
  };

  type addAvailableModelCfgParams = {
    setting_id: string;
    name: string;
    type: string;
  };

  /**
   * 创建会话的参数。
   * @param {string | null} [title] - 会话的标题，可选。
   * @param {string} model - 使用的模型名称。
   * @param {string} system_prompt - 系统提示。
   * @param {number} temperature - 控制生成文本的随机性。
   * @param {string[] | null} [knowledge_base_ids] - 绑定的知识库ID列表，可选。
   */
  type BaseConversationParams = {
    title?: string | null;
    system_prompt: string;
    temperature: number;
    knowledge_base_ids?: string[] | null;
  };
  
    /**
 * 创建会话的参数。
 * @param {string | null} [title] - 会话的标题，可选。
 * @param {string} available_model_id - 使用的模型ID。
 * @param {string} system_prompt - 系统提示。
 * @param {number} temperature - 控制生成文本的随机性。
 * @param {string[] | null} [knowledge_base_ids] - 绑定的知识库ID列表，可选。
 * @param {number | null} [use_memory] - 是否使用记忆功能，可选。
 * @param {Record<string, unknown> | null} [mcp_server_configs] - MCP服务器配置，可选。
 */
type CreateConversationParams = {
  title?: string | null;
  available_model_id: string;
  system_prompt: string;
  temperature: number;
  knowledge_base_ids?: string[] | null;
  use_memory?: number | null;
  mcp_server_configs?: Record<string, unknown> | null;
};

/**
 * 更新会话的参数。
 * @param {string} conv_id - 要更新的会话ID。
 * @param {string | null} [title] - 新的会话标题，可选。
 * @param {string | null} [available_model_id] - 新的模型ID，可选。
 * @param {string | null} [system_prompt] - 新的系统提示，可选。
 * @param {number | null} [temperature] - 新的温度值，可选。
 * @param {string[] | null} [knowledge_base_ids] - 新的知识库ID列表，可选。
 * @param {number | null} [use_memory] - 是否使用记忆功能，可选。
 * @param {Record<string, unknown> | null} [mcp_server_configs] - MCP服务器配置，可选。
 */
type UpdateConversationParams = {
  conv_id: string;
  title?: string | null;
  available_model_id?: string | null;
  system_prompt?: string | null;
  temperature?: number | null;
  knowledge_base_ids?: string[] | null;
  use_memory?: number | null;
  mcp_server_configs?: Record<string, unknown> | null;
};

  /**
   * 删除会话的参数。
   * @param {string} conv_id - 要删除的会话ID。
   */
  type DeleteConversationParams = {
    conv_id: string;
  };

  /**
   * 列出会话的参数。
   * @param {number} [page] - 页码，可选，默认为1。
   * @param {number} [size] - 每页的会话数量，可选，默认为10。
   */
  type ListConversationsParams = {
    page?: number;
    size?: number;
  };

  /**
 * 发送消息的参数。
 * @param {string} conv_id - 会话ID。
 * @param {string} message - 要发送的消息内容。
 * @param {number | null} [temperature] - 消息生成的温度值，可选。
 * @param {number | null} [max_tokens] - 消息生成的最大令牌数，可选。
 * @param {boolean} [search] - 是否启用搜索功能，可选，默认为 false。
 */
type SendMessageParams = {
  conv_id: string;
  message: string;
  temperature?: number | null;
  max_tokens?: number | null;
  search?: boolean;
  thinking?: boolean;
};

  /**
   * 获取消息历史的参数。
   * @param {string} conv_id - 会话ID。
   * @param {number} [limit] - 返回的消息数量限制，可选，默认为100。
   */
  type GetMessageHistoryParams = {
    conv_id: string;
    limit?: number;
  };

  /**
   * 清除消息历史的参数。
   * @param {string} conv_id - 会话ID。
   */
  type ClearMessageHistoryParams = {
    conv_id: string;
  };

  /**
   * 与模型对话的参数。
   * @param {Message[]} messages - 对话历史中的消息数组。
   * @param {boolean} [stream] - 是否启用流式输出，可选，默认为false。
   * @param {number} [temperature] - 生成文本的温度值，可选，默认为1。
   * @param {number | null} [max_tokens] - 生成的最大令牌数，可选。
   * @param {string | null} [model] - 使用的模型名称，可选。
   */
  type ChatRequestParams = {
    messages: Message[];
    stream?: boolean;
    temperature?: number;
    max_tokens?: number | null;
    model?: string | null;
  };

  /**
   * 对话消息类型。
   * @param {string} role - 消息发送者的角色，'user' 或 'assistant'。
   * @param {string} content - 消息内容。
   */
  type Message = {
    role: 'user' | 'assistant';
    content: string;
  };
  // 上传知识库文件的请求参数
  type UploadKnowledgeFileParams = {
    file: File; // 上传的文件
  };

  // 执行知识库文件的请求参数
  type ExecuteKnowledgeFileParams = {
    kb_id: string; // 知识库ID
    file_object_names: string[]; // 文件对象名称列表
    auto: boolean; // 是否自动执行
    chunk_size: number; // 切片大小
    repeat_size: number; // 重复切片大小
    separator: string; // 分隔符
  };

  // 列出知识库文件的查询参数
  type ListKnowledgeFilesParams = {
    kb_id: string; // 知识库ID
    page?: number; // 页码，默认为1
    size?: number; // 每页大小，默认为10
  };

  // 删除知识库文件的查询参数
  type DeleteKnowledgeFileParams = {
    id: string; // 文件ID
  };
  
  // 知识库创建请求体参数
  type KnowledgeCreate = {
    /** 知识库名称 */
    name: string;
    /** 知识库描述信息 */
    desc?: string;
    /** 可用向量化模型ID */
    available_model_id?: string;
    /** collection名称 */
    collection_name?: string;
    /** index名称 */
    index_name?: string;
    /** 是否开启布局识别，默认为0 */
    enable_layout?: number;
  };

  // 知识库更新请求体参数
  type KnowledgeUpdate = {
    /** 主键ID */
    id: string;
    /** 新更新知识库名称 */
    name?: string;
    /** 新更新知识库描述 */
    desc?: string;
  };

  // 知识库分页列表查询参数
  type KnowledgeListParams = {
    /** 知识库名称，用于搜索 */
    name?: string;
    /** 页码数，默认为1 */
    page?: number;
    /** 页面记录数量，默认为10 */
    size?: number;
  };
  
  type bqbDislikesParams = {
    /** Key */
    key: string;
  };

  type bqbLikesParams = {
    /** Key */
    key: string;
  };

  type bqbListParams = {
    /** 名称 */
    name?: string;
    /** 页码数 */
    page?: number;
    /** 页面记录数量 */
    size?: number;
  };

  type emailCodeParams = {
    email: string;
  };

  type EmailCodeSchema = {
    /** Account 账号 */
    account: string;
    /** Code 验证码 */
    code: string;
  };

  type HTTPValidationError = {
    /** Detail */
    detail?: ValidationError[];
  };

  type JWTOutSchema = {
    /** Access Token */
    access_token: string;
    /** Refresh Token */
    refresh_token: string;
    /** Token Type */
    token_type: string;
  };

  type LoginEmailSchema = {
    /** Email 邮箱地址 */
    email: string;
    /** Code 验证码 */
    code: string;
    /** Remember 自动登录 */
    remember?: boolean;
  };

  type LoginSchema = {
    /** Account 账号 */
    account: string;
    /** Password 登陆密码 */
    password: string;
    /** Captcha 验证码 */
    captcha: string;
    /** Remember 自动登录 */
    remember?: boolean;
  };

  type Success = {
    /** Code */
    status_code?: number;
    /** Msg */
    status_message?: string;
    /** Data */
    data?: any | any[] | string | null;
  };

  type SuccessBool_ = {
    /** Code */
    code?: number;
    /** Msg */
    msg?: string;
    /** Data */
    data?: boolean | any[] | string | null;
  };

  type SuccessJWTOutSchema_ = {
    /** Code */
    code?: number;
    /** Msg */
    msg?: string;
    /** Data */
    data?: JWTOutSchema | any[] | string | null;
  };

  type SuccessStr_ = {
    /** Code */
    code?: number;
    /** Msg */
    msg?: string;
    /** Data */
    data?: string | any[] | null;
  };

  type SuccessUnionBool_str_ = {
    /** Code */
    code?: number;
    /** Msg */
    msg?: string;
    /** Data */
    data?: boolean | string | any[] | null;
  };

  type validateCaptchaParams = {
    code: string;
  };

  type ValidationError = {
    /** Location */
    loc: (string | number)[];
    /** Message */
    msg: string;
    /** Error Type */
    type: string;
  };
  
  /**
   * OpenAPI 配置列表项
   */
  type OpenApiConfig = {
    /** 配置ID */
    id: string;
    /** 配置名称 */
    name: string;
    /** 配置描述 */
    description: string;
    /** 基础URL */
    base_url: string;
    /** 工具数量 */
    tools_count: number;
    /** 是否有凭证 */
    has_credentials: boolean;
    /** 创建时间 */
    created_at: string;
    /** 更新时间 */
    updated_at: string;
  };

  /**
   * OpenAPI 工具信息
   */
  type OpenApiTool = {
    /** 工具ID */
    id: string;
    /** 工具名称 */
    name: string;
    /** 工具描述 */
    description: string;
    /** 请求方法 */
    method: string;
    /** 请求路径 */
    path: string;
    /** 创建时间 */
    created_at: string;
  };

  /**
   * OpenAPI 配置详情
   */
  type OpenApiConfigDetail = {
    /** 配置ID */
    id: string;
    /** 配置名称 */
    name: string;
    /** 配置描述 */
    description: string;
    /** 基础URL */
    base_url: string;
    /** 是否有凭证 */
    has_credentials: boolean;
    /** 创建时间 */
    created_at: string;
    /** 更新时间 */
    updated_at: string;
    /** 工具列表 */
    tools: OpenApiTool[];
  };

  /**
   * OpenAPI 配置列表响应
   */
  type OpenApiConfigsList = {
    /** 总数 */
    total: number;
    /** 数据列表 */
    data: OpenApiConfig[];
  };

  /**
   * OpenAPI 配置工具列表响应
   */
  type OpenApiConfigToolsList = {
    /** 总数 */
    total: number;
    /** 数据详情 */
    data: OpenApiConfigDetail;
  };

  /**
   * 删除OpenAPI配置响应
   */
  type DeleteOpenApiConfigResponse = {
    /** 状态码 */
    status_code: number;
    /** 状态消息 */
    status_message: string;
    /** 数据 */
    data: {
      /** 配置ID */
      config_id: string;
      /** 消息 */
      message: string;
    };
  };
  
  /**
   * 创建OpenAPI配置请求数据
   */
  type CreateOpenApiConfigData = {
    /** 配置名称 */
    name: string;
    /** OpenAPI规范 */
    openapi_spec: Record<string, any>;
    /** 凭证 */
    credentials: string;
    /** 描述 */
    description: string;
  };
  
  /**
   * 创建OpenAPI配置响应数据中的工具信息
   */
  type CreatedOpenApiTool = {
    /** 工具ID */
    id: string;
    /** 工具名称 */
    name: string;
    /** 工具描述 */
    description: string;
    /** 请求方法 */
    method: string;
    /** 请求路径 */
    path: string;
    /** 创建时间 */
    created_at: string;
  };
  
  /**
   * 创建OpenAPI配置响应
   */
  type CreateOpenApiConfigResponse = {
    /** 状态码 */
    status_code: number;
    /** 状态消息 */
    status_message: string;
    /** 数据 */
    data: {
      /** 配置ID */
      config_id: string;
      /** 配置名称 */
      config_name: string;
      /** 基础URL */
      base_url: string;
      /** 工具数量 */
      tools_count: number;
      /** 工具列表 */
      tools: CreatedOpenApiTool[];
    };
  };
}
