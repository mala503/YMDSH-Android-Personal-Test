import * as McpClient from '@deepseek-ai/dsh-mcp-client';
import { fileURLToPath } from 'node:url';

export const name = 'dsh-computer-use-android';
export const inject = ['tools'];
export async function apply(ctx) {
  const config = {transport:'stdio',serverName:'dsha-android',
    command:process.execPath,args:[fileURLToPath(new URL('./server.cjs',import.meta.url))],
    failOnStartupError:true,toolCallTimeoutMs:180000,reconnect:{enabled:false}};
  let child;
  ctx.effect(function* () {
    child = ctx.plugin(McpClient,config);
    yield child.dispose;
  },'dsha-android-computer-use');
  await child.await();
}
