import torch

from activation import TReLU
from model import HiddenBlock

def train(dataloader, model, loss_fn, optimizer, epoch, device, writer=None):
    num_total_steps = len(dataloader)
    size = len(dataloader.dataset)
    model.train()

    for i, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)

        # Compute prediction error
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backpropagation
        loss.backward()
        optimizer.step()

        if i % 100 == 0:
            write_grads_and_alphas(model, epoch, i, num_total_steps, writer)

        optimizer.zero_grad()

        if i % (2**5) == 0:
            write_loss(loss, size, epoch, i, len(X), num_total_steps, writer)


def write_grads_and_alphas(model, cur_epoch, cur_iter, num_total_steps, writer):
    weight_grads = []
    bias_grads = []
    alphas = []
    for module in model.net:
        if isinstance(module, HiddenBlock):
            weight_grads.append(module.linear.weight.grad.ravel())
            bias_grads.append(module.linear.bias.grad.ravel())
            if isinstance(module.activation, TReLU):
                for param in module.activation.parameters():
                    alphas.append(param.data.item())

        elif isinstance(module, torch.nn.Linear):
            weight_grads.append(module.weight.grad.ravel())
            bias_grads.append(module.bias.grad.ravel())
        elif isinstance(module, TReLU):
            for param in module.parameters():
                alphas.append(param.data.item())

    weight_grad_norms = torch.linalg.norm(torch.cat(weight_grads))
    bias_grad_norms = torch.linalg.norm(torch.cat(bias_grads))
    print()
    print('Weight grads norm:', weight_grad_norms.item())
    print('Bias grads norm:', bias_grad_norms.item())

    if model.beta is not None:
        if model.beta_is_global:
            print('Residual Connection Global Beta:', model.beta.item())
        else:
            print('Residual Connection Betas:', [b.item() for b in model.beta])

    if writer:
        writer.add_scalar('Weights Gradient Norms', weight_grad_norms.item(), num_total_steps * cur_epoch + cur_iter)
        writer.add_scalar('Bias Gradient Norms', bias_grad_norms.item(), num_total_steps * cur_epoch + cur_iter)
        if model.beta is not None:
            if model.beta_is_global:
                writer.add_scalar('Global Beta', model.beta.item(), num_total_steps * cur_epoch + cur_iter)
            else:
                for i, b in enumerate(model.beta):
                    writer.add_scalar(f'Betas/Beta_{i}', b.item(), num_total_steps * cur_epoch + cur_iter)
    print('TReLU alphas:', ["{:.5f}".format(alpha) for alpha in alphas])
    print()


def write_loss(loss, size, cur_epoch, cur_iter, size_batch, num_total_steps, writer=None):
    loss, current = loss.item(), (cur_iter + 1) * size_batch
    if writer:
        writer.add_scalar('Training Loss', loss, num_total_steps * cur_epoch + cur_iter)
    print(f"Loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")