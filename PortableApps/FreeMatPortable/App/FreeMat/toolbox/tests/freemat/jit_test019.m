function A = jit_test019
  A = 150000;
  C = 0;
  for b=1:A
    C = C + b;
  end
  A = C;
