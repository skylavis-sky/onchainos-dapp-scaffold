// my-dex-swap — onchainOS DApp Skill
// 由 onchainos-dapp-scaffold 生成（严格遵循 onchainOS Skill 方案规范）。
//
// DApp 开发者仅需在 TODO [三方] 注释处填入业务逻辑。
// 严禁引入 ethers.Wallet / signTransaction / sendTransaction / 本地私钥。

type PendingSign = {
  status: 'pending_sign';
  unsigned_tx: {
    to: string;
    data: string;
    value: string;
    chain: string;
  };
  description: string;
  next_action: { tool: string; reason?: string };
};

type SwapParams = {
  from: string;
  to: string;
  amount: string;
  chain?: string;
};

async function my_build_swap(params: SwapParams): Promise<PendingSign> {
  // TODO [三方] 业务逻辑：查路由、构造 calldata
  const route = await myApi.getRoute(params.from, params.to, params.amount);
  const calldata = encodeSwapCalldata(route);

  // [固定] 返回 pending_sign 外壳，不可改动
  return {
    status: 'pending_sign',
    unsigned_tx: {
      to: route.contractAddress,
      data: calldata,
      value: '0',
      chain: params.chain ?? 'eip155:1',
    },
    description: `Swap ${params.amount} ${params.from} → ${params.to}`,
    next_action: { tool: 'onchainos wallet contract-call' },
  };
}

// TODO [三方] 补充 myApi / encodeSwapCalldata 实现
declare const myApi: {
  getRoute(from: string, to: string, amount: string): Promise<{ contractAddress: string }>;
};
declare function encodeSwapCalldata(route: unknown): string;

export { my_build_swap };
